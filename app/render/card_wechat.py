"""办事卡片渲染（设计文档 第四章·界面形态 / 附录D）。

服务端按模板渲染，模型不直接控制排版。
"""
from __future__ import annotations

from app.config import settings
from app.schemas.card import ActionCard, Refusal

DIVIDER = "─────────────────────"


def render_card(card: ActionCard) -> str:
    """将结构化办事卡片渲染为微信文本消息。"""
    lines = [f"📋 {card.matter_name}", DIVIDER]
    if card.target_users:
        lines.append("适用对象：" + "、".join(card.target_users))

    if card.materials:
        lines.append("✅ 所需材料")
        for m in card.materials:
            note = f"（{m.note}）" if m.note else ""
            lines.append(f"  ☐ {m.item}{note}")

    lines.append(DIVIDER)
    lines.append(f"📍 办理地点：{card.location}")
    lines.append(f"🕐 办公时间：{card.office_hours}")
    lines.append(f"⏰ 截止日期：{card.deadline or '未查到明确期限'}")
    lines.append(f"🧭 办理方式：{card.channel}")
    lines.append(f"☎️ 咨询渠道：{card.contact or '未查到'}")

    if card.sources:
        lines.append(DIVIDER)
        for s in card.sources:
            date_str = s.date.isoformat() if s.date else ""
            lines.append(f"📎 出处：《{s.title}》{s.issuer} {date_str}".rstrip())

    for note in card.notes:
        lines.append(f"💡 {note}")
    if card.confidence < settings.confidence_warn_threshold:
        lines.append("⚠️ 信息可能不完整，建议向相关部门确认")

    return "\n".join(lines)


def render_refusal(refusal: Refusal) -> str:
    """拒答说明（文字气泡）。"""
    return f"很抱歉，{refusal.message}"


def render_text(text: str) -> str:
    """简短口语化回应（打招呼 / 澄清追问）。"""
    return text
