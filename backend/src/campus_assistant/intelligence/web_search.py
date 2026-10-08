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
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None):
        super().__init__(transport)
        self._key = api_key

    async def search(self, school: School, question: str, category: str | None):
        if not self._key:
            raise SearchUnavailable()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=4),
                                         transport=self.transport, follow_redirects=False) as client:
                async def fetch():
                    async with client.stream("POST", "https://api.tavily.com/search",
                                             headers={"Authorization": "Bearer " + self._key},
                                             json={"query": f"{school.name} {category or ''} {question[:350]}",
                                                   "include_domains": [school.domain],
                                                   "include_domains_mode": "restrict",
                                                   "search_depth": "basic", "max_results": 5,
                                                   "include_answer": False, "include_raw_content": False,
                                                   "auto_parameters": False}) as response:
                        response.raise_for_status()
                        raw = bytearray()
                        async for chunk in response.aiter_bytes():
                            raw.extend(chunk)
                            if len(raw) > 262144:
                                raise ValueError("Search response too large")
                        import json
                        return json.loads(raw)
                data = await asyncio.wait_for(fetch(), timeout=12)
            results, seen = [], set()
            now = datetime.now(UTC).isoformat()
            if not isinstance(data.get("results"), list):
                raise TypeError("Missing search results")
            for result in data["results"][:10]:
                url = str(result.get("url", ""))
                title = str(result.get("title", ""))[:250]
                snippet = str(result.get("content", ""))[:1500]
                if not official_url(url, school.domain) or url in seen or not title or not snippet:
                    continue
                seen.add(url)
                results.append(WebSource(id=f"web-{len(results) + 1}", title=title, url=url,
                                         snippet=snippet, retrieved_at=now))
                if len(results) == 5:
                    break
            return results
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError, AttributeError):
            raise SearchUnavailable() from None
