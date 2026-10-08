import re

from campus_assistant.schemas.chat import ChatRequest
from campus_assistant.schemas.knowledge import KnowledgeEntry


def normalize(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.casefold())


def retrieve(request: ChatRequest, entries: list[KnowledgeEntry]) -> list[KnowledgeEntry]:
    """首轮事项别名闸门，不冒充语义检索或相关度置信模型。"""
    query = normalize(request.question)
    hits = []
    for entry in entries:
        if request.category and entry.category != request.category:
            continue
        terms = [normalize(term) for term in entry.aliases]
        # 过短别名容易让无关问题误命中。
        score = max((len(term) for term in terms if len(term) >= 2 and term in query), default=0)
        if score:
            hits.append((score, entry))
    return [entry for _, entry in sorted(hits, key=lambda hit: -hit[0])]
