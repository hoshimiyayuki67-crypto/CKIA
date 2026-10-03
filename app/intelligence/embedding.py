"""嵌入模型（智能层）。BGE 系列中文嵌入，开源可本地部署。"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    """生成归一化向量，采用余弦相似度检索。"""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
