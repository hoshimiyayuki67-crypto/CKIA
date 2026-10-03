"""混合检索与重排序（智能层，设计文档 第五章·3）。

向量检索（语义匹配）+ BM25 关键词检索（专有名词精确匹配），官方层优先。
"""
from __future__ import annotations

from app.config import settings
from app.data import vector_store
from app.intelligence import embedding, reranker
from app.schemas.knowledge import RetrievedChunk


def hybrid_search(
    query: str, category: str | None = None, layer: str = "official"
) -> list[RetrievedChunk]:
    """混合检索：官方层优先召回，官方层无结果时才检索经验层。"""
    query_vec = embedding.embed([query])[0]
    hits = vector_store.search(
        query_vec, top_k=settings.retrieval_top_k, category=category, layer=layer
    )
    if not hits and layer == "official":
        hits = vector_store.search(
            query_vec, top_k=settings.retrieval_top_k, category=category, layer="experience"
        )
    # TODO 融合 BM25 关键词检索结果（RRF 或加权求和），保证专有名词不漏
    return hits


def rerank(query: str, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """重排序入口。"""
    return reranker.rerank(query, hits)


def top_score(hits: list[RetrievedChunk]) -> float:
    """最高相关度，用于阈值判定。"""
    return max((h.score for h in hits), default=0.0)
