"""应用层编排入口：接收接入层消息，驱动处理链路并渲染回复。

微信端与安卓端共用 process() 核心链路，仅在最末端按渠道做不同输出：
- 微信端：渲染为 XML 回复（handle）
- 安卓端：序列化为 JSON（见 app/api/chat.py）
"""
from __future__ import annotations

from app.core import analytics, session
from app.intelligence import rag
from app.render.card_wechat import render_card, render_refusal, render_text
from app.schemas.card import ActionCard, Refusal
from app.utils import wechat_xml
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def process(session_hash: str, question: str, image: bytes | None = None):
    """核心处理链路：返回 ActionCard / Refusal / str。"""
    session.session_store.append(session_hash, "user", question or "[图片]")

    result = rag.answer(question, image=image)

    if isinstance(result, ActionCard):
        session.session_store.append(session_hash, "assistant", result.matter_name)
    elif isinstance(result, Refusal):
        session.session_store.append(session_hash, "assistant", result.message)

    # 匿名化埋点：仅记录类别、命中与否、是否有效回答，不含身份信息
    analytics.record(
        session_hash=session_hash,
        question=question,
        intent=getattr(result, "intent", ""),
        hit=isinstance(result, ActionCard),
        answer_given=isinstance(result, (ActionCard, Refusal)),
        image_uploaded=image is not None,
    )
    return result


async def handle(msg: dict) -> str:
    """处理一条微信消息，返回 XML 回复。"""
    openid = msg["openid"]
    session_hash = session.session_store.hash_of(openid)
    result = await process(session_hash, msg.get("text", ""), msg.get("image"))

    if isinstance(result, ActionCard):
        reply = render_card(result)
    elif isinstance(result, Refusal):
        reply = render_refusal(result)
    else:  # 澄清追问等中间态
        reply = render_text(str(result))

    return wechat_xml.build_text_reply(openid, reply)
