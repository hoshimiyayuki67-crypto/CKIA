"""字段抽取与校验（设计文档 第五章·3、附录C）。

三段式约束：格式约束（JSON）-> 字段抽取 -> 校验 / 重试 / 降级。
"""
from __future__ import annotations

import json
from datetime import date

from app.schemas.knowledge import RetrievedChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    "matter_name",
    "target_users",
    "materials",
    "location",
    "office_hours",
    "channel",
    "contact",
    "sources",
]


def parse_json(draft: str) -> dict:
    """解析模型输出：解析失败时尝试提取 JSON 片段，而非直接报错。"""
    try:
        return json.loads(draft)
    except json.JSONDecodeError:
        start, end = draft.find("{"), draft.rfind("}")
        if start != -1 and end != -1:
            return json.loads(draft[start : end + 1])
        raise


def extract(draft: str, hits: list[RetrievedChunk]) -> dict:
    """字段抽取：从受限生成的 JSON 草稿中抽取卡片字段。

    TODO 接入 LLM 结构化输出；解析失败时追加"仅输出 JSON"指令重试一次，
    仍失败则降级为纯文本答案并标注"格式解析失败"。
    """
    return parse_json(draft)


def validate(fields: dict) -> dict:
    """字段级校验（附录C 校验规则）。不合法字段统一兜底，绝不自行填充。"""
    # deadline：必须为合法日期且不早于当前日期，否则视为疑似过期
    deadline = fields.get("deadline")
    if deadline:
        try:
            if date.fromisoformat(str(deadline)) < date.today():
                fields.setdefault("notes", []).append("所标期限疑似已过期，请核实")
                fields["deadline"] = None
        except ValueError:
            fields["deadline"] = None

    # confidence：必须落在 0-1 之间，越界归零
    conf = fields.get("confidence", 0.0)
    if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
        fields["confidence"] = 0.0

    return fields
