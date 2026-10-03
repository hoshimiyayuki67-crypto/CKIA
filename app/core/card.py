"""卡片组装（应用层）。将抽取并校验后的字段组装为结构化办事卡片。"""
from __future__ import annotations

from app.schemas.card import UNKNOWN, ActionCard, Material, SourceRef
from app.schemas.knowledge import RetrievedChunk


def _materials(raw: list | None) -> list[Material]:
    result: list[Material] = []
    for item in raw or []:
        if isinstance(item, str):
            result.append(Material(item=item))
        elif isinstance(item, dict):
            result.append(Material(**item))
    return result


def build_card(fields: dict, sources: list[RetrievedChunk]) -> ActionCard:
    """按字段规范组装卡片。

    缺失字段以「未查到明确信息」兜底；sources 以检索命中为唯一依据，模型不得增删。
    """
    refs = [SourceRef(title=s.title, issuer=s.issuer, date=s.publish_date) for s in sources]
    return ActionCard(
        matter_name=fields.get("matter_name") or UNKNOWN,
        target_users=fields.get("target_users") or [],
        materials=_materials(fields.get("materials")),
        location=fields.get("location") or UNKNOWN,
        office_hours=fields.get("office_hours") or UNKNOWN,
        deadline=fields.get("deadline"),
        channel=fields.get("channel") or "未查到",
        contact=fields.get("contact") or "",
        sources=refs,
        notes=fields.get("notes") or [],
        confidence=float(fields.get("confidence", 0.0)),
    )
