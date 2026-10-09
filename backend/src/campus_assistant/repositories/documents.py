"""Reference document retrieval, isolated from reviewed executable card fields."""
import math
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from campus_assistant.schemas.chat import Source


class DocumentChunk(BaseModel):
    model_config = ConfigDict(extra='forbid')
    school_id: str
    version: str
    reference_only: bool = True
    text: str = Field(min_length=1, max_length=12000)
    source: Source


def tokens(text):
    text = re.sub(r'需要|准备|哪些|怎么|如何|什么|可以|办理|请问|一下|关于|告诉|帮我|多少|的|了|呢|吗|？', '', text.lower())
    words = re.findall(r'[\u4e00-\u9fff]+|[a-z0-9]+', text)
    return [part for word in words for part in
            ([word] if len(word) < 2 or word.isascii() else [word[i:i+2] for i in range(len(word)-1)])]


def retrieve_documents(question, documents, school_id, limit=6):
    documents = [d for d in documents if d.school_id == school_id]
    query = set(tokens(question))
    if not query or not documents:
        return []
    counters = [Counter(tokens(d.source.title + '\n' + d.text)) for d in documents]
    frequency = Counter(term for counter in counters for term in counter)
    average = sum(sum(c.values()) for c in counters) / len(counters)
    ranked = []
    for document, counter in zip(documents, counters, strict=True):
        score = 0
        for term in query & counter.keys():
            count = counter[term]
            idf = math.log(1 + (len(documents) - frequency[term] + .5) / (frequency[term] + .5))
            score += idf * count * 2.2 / (count + 1.2 * (.25 + .75 * sum(counter.values()) / average))
        for term in query & set(tokens(document.source.title)):
            score += 2 * math.log(1 + (len(documents) - frequency[term] + .5) / (frequency[term] + .5))
        if score > .6:
            ranked.append((score, document))
    return [d for _, d in sorted(ranked, key=lambda pair: -pair[0])[:limit]]
