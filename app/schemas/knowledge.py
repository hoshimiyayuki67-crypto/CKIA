"""知识库条目结构（设计文档 第五章·数据结构设计）。

双层知识库通过 layer 字段物理隔离：official（官方层）/ experience（经验层）。
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel

Layer = Literal["official", "experience"]
Category = Literal["资助", "教务", "财务", "学籍", "就业", "生活"]


class KnowledgeChunk(BaseModel):
    """入库的知识库片段。"""

    doc_id: str
    title: str
    issuer: str
    publish_date: Optional[date] = None
    category: Category
    layer: Layer = "official"
    chunk_id: str
    chunk_text: str
    vector: Optional[list[float]] = None
    valid_until: Optional[date] = None


class RetrievedChunk(KnowledgeChunk):
    """带检索分数的召回片段。"""

    score: float = 0.0
