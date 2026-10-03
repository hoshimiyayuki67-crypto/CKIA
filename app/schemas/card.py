"""办事卡片结构（设计文档 第五章·数据结构设计 / 附录D）。

字段抽不到时统一填「未查到明确信息」，绝不自行填充。
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

UNKNOWN = "未查到明确信息"


class Material(BaseModel):
    """材料清单条目。"""

    item: str
    required: bool = True
    note: Optional[str] = None


class SourceRef(BaseModel):
    """信息来源：文件名 + 发布部门 + 日期。"""

    title: str
    issuer: str
    date: Optional[date] = None


class ActionCard(BaseModel):
    """结构化办事卡片。"""

    matter_name: str
    target_users: list[str] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    location: str = UNKNOWN
    office_hours: str = UNKNOWN
    deadline: Optional[date] = None
    channel: str = "未查到"
    contact: str = ""
    sources: list[SourceRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class Refusal(BaseModel):
    """拒答结果：检索不到依据时返回，并给出咨询出路。"""

    intent: str
    message: str
    contact: str = ""
