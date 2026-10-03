"""重排模型（智能层）。对候选片段二次排序，提升 Top-K 精度。"""
from __future__ import annotations

import math
from functools import lru_cache

from app.config import settings
from app.schemas.knowledge import RetrievedChunk


@lru_cache
def _model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.rerank_model)


def rerank(query: str, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """按相关度重排（降序）。CrossEncoder 输出经 sigmoid 归一化到 0-1。"""
    if not hits:
        return []
    scores = _model().predict([(query, h.chunk_text) for h in hits])
    for hit, score in zip(hits, scores):
        hit.score = 1 / (1 + math.exp(-float(score)))
    return sorted(hits, key=lambda h: h.score, reverse=True)
