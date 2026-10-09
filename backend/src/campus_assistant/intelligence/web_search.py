"""Bounded, keyless search adapter. Never fetch arbitrary result URLs.

Bing RSS is a best-effort endpoint; failures are explicit and never replaced by
made-up sources. A documented provider can replace this adapter independently.
"""
import asyncio
import os
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from campus_assistant.schemas.chat import WebSource
from campus_assistant.services.schools import School


class SearchUnavailable(Exception):
    pass


def official_url(url: str, domain: str) -> bool:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        return (parsed.scheme in {"http", "https"} and not parsed.username
                and not parsed.password and parsed.port in {None, 80, 443}
                and (host == domain or host.endswith("." + domain)))
    except ValueError:
        return False


class WebSearch:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self.transport = transport

    @classmethod
    def from_environment(cls):
        key = os.getenv("TAVILY_API_KEY", "").strip()
        return TavilySearch(key)

    async def search(self, school: School, question: str, category: str | None):
        # Strip caller search operators: official domain is always imposed by server.
        terms = re.sub(r"(?:site|filetype|inurl|intitle):\S+", "", question,
                       flags=re.IGNORECASE)
        terms = re.sub(r"[\"'<>|{}]", " ", terms)[:350]
        query = f"site:{school.domain} {school.name} {category or ''} {terms}"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=4),
                                         transport=self.transport, follow_redirects=False) as client:
                async def fetch():
                    async with client.stream("GET", "https://www.bing.com/search",
                                             params={"q": query, "format": "rss", "count": "10"},
                                             headers={"User-Agent": "CampusAssistant/0.4"}) as response:
                        response.raise_for_status()
                        chunks = bytearray()
                        async for chunk in response.aiter_bytes():
                            chunks.extend(chunk)
                            if len(chunks) > 262144:
                                raise ValueError("Search response too large")
                        return bytes(chunks)
                raw = await asyncio.wait_for(fetch(), timeout=12)
            if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
                raise ValueError("Unexpected XML declarations")
            root = ET.fromstring(raw)
            if root.tag != "rss":
                raise ValueError("Not a search feed")
            results, seen = [], set()
            now = datetime.now(UTC).isoformat()
            for item in root.findall("./channel/item")[:20]:
                url = (item.findtext("link") or "").strip()
                if url in seen or not official_url(url, school.domain):
                    continue
                title = re.sub(r"<[^>]+>", "", item.findtext("title") or "")[:250]
                snippet = re.sub(r"<[^>]+>", "", item.findtext("description") or "")[:1500]
                if not title or not snippet:
                    continue
                seen.add(url)
                results.append(WebSource(id=f"web-{len(results) + 1}", title=title,
                                         url=url, snippet=snippet, retrieved_at=now))
                if len(results) == 5:
                    break
            return results
        except (httpx.HTTPError, TimeoutError, ValueError, ET.ParseError):
            raise SearchUnavailable() from None


class TavilySearch(WebSearch):
    """Advanced search, full-text extraction and bounded same-school traversal."""
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None):
        super().__init__(transport)
        self._key = api_key
        self._cache = {}

    async def _post(self, client, endpoint, payload):
        import json
        async with client.stream("POST", "https://api.tavily.com/" + endpoint,
                                 headers={"Authorization": "Bearer " + self._key},
                                 json=payload) as response:
            response.raise_for_status()
            raw = bytearray()
            async for chunk in response.aiter_bytes():
                raw.extend(chunk)
                if len(raw) > 1048576:
                    raise ValueError("Search response too large")
            return json.loads(raw)

    async def search(self, school: School, question: str, category: str | None):
        if not self._key:
            raise SearchUnavailable()
        import time
        cache_key = (school.domain, school.name, question, category)
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < 600:
            return [source.model_copy(deep=True) for source in cached[1]]
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(14, connect=4),
                                         transport=self.transport, follow_redirects=False) as client:
                async def research():
                    data = await self._post(client, "search", {
                        "query": f"{school.name} {category or ''} {question[:350]}",
                        "include_domains": [school.domain], "include_domains_mode": "restrict",
                        "search_depth": "advanced", "max_results": 6, "chunks_per_source": 3,
                        "include_answer": False, "include_raw_content": "markdown",
                        "auto_parameters": False})
                    results, seen = [], set()
                    now = datetime.now(UTC).isoformat()
                    if not isinstance(data.get("results"), list):
                        raise TypeError("Missing search results")
                    for item in data["results"][:12]:
                        url = str(item.get("url", ""))
                        title = str(item.get("title", ""))[:250]
                        content = item.get("raw_content") or item.get("content") or ""
                        if (not official_url(url, school.domain) or url in seen
                                or not title or not isinstance(content, str) or not content.strip()):
                            continue
                        seen.add(url)
                        results.append(WebSource(id=f"web-{len(results) + 1}", title=title,
                            url=url, snippet=content[:6000], retrieved_at=now,
                            content_kind="page" if item.get("raw_content") else "snippet"))
                        if len(results) == 6:
                            break
                    if not results:
                        return results

                    async def enrich():
                        try:
                            extracted = await self._post(client, "extract", {
                                "urls": [s.url for s in results[:3]], "query": question[:350],
                                "chunks_per_source": 5, "extract_depth": "advanced",
                                "format": "markdown", "timeout": 10})
                            for item in extracted.get("results", []):
                                url, content = item.get("url"), item.get("raw_content")
                                if not isinstance(content, str) or not content.strip():
                                    continue
                                for source in results:
                                    if source.url == url and official_url(url, school.domain):
                                        source.snippet = content[:6000]
                                        source.content_kind = "page"
                        except (httpx.HTTPError, TimeoutError, ValueError, TypeError, AttributeError):
                            pass  # Full text is optional; search evidence remains usable.

                    async def traverse():
                        try:
                            crawled = await self._post(client, "crawl", {
                                "url": results[0].url, "instructions": question[:350],
                                "max_depth": 2, "max_breadth": 3, "limit": 3,
                                "select_domains": [r"^(.*\.)?" + re.escape(school.domain) + "$"],
                                "allow_external": False, "extract_depth": "advanced",
                                "format": "markdown", "timeout": 10})
                            return crawled.get("results", [])
                        except (httpx.HTTPError, TimeoutError, ValueError, TypeError, AttributeError):
                            return []

                    _, pages = await asyncio.gather(enrich(), traverse())
                    # Retain strongest initial hits plus up to two additional internal pages.
                    for item in pages[:6]:
                        url, content = item.get("url", ""), item.get("raw_content", "")
                        if (url in seen or not official_url(url, school.domain)
                                or not isinstance(content, str) or not content.strip()):
                            continue
                        seen.add(url)
                        if len(results) >= 6:
                            results.pop()
                        results.insert(3, WebSource(id="pending", title=str(item.get("title") or
                            "官网相关正文")[:250], url=url, snippet=content[:6000],
                            retrieved_at=now, content_kind="page"))
                        if len(seen) >= len(data["results"]) + 2:
                            break
                    for i, source in enumerate(results):
                        source.id = f"web-{i + 1}"
                    return results
                results = await asyncio.wait_for(research(), timeout=32)
            if len(self._cache) >= 64:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = (time.monotonic(), [s.model_copy(deep=True) for s in results])
            return results
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError, AttributeError):
            raise SearchUnavailable() from None
