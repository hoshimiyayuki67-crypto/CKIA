"""接入层：微信公众号 / 企业微信消息接入（设计文档 第五章·总体架构）。

职责：
- 处理微信服务器 URL 校验（GET）；
- 接收用户消息（文本 / 图片），交应用层编排处理；
- 将处理结果（文字气泡 / 办事卡片）下发。
"""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, Query, Request, Response

from app.config import settings
from app.core import agent
from app.utils import wechat_xml
from app.utils.logger import get_logger

router = APIRouter(prefix="/wechat", tags=["接入层"])
logger = get_logger(__name__)


def _check_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """微信服务器签名校验。"""
    parts = sorted([settings.wechat_token, timestamp, nonce])
    digest = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return digest == signature


@router.get("", summary="微信服务器 URL 校验")
async def verify(
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
) -> Response:
    if not _check_signature(signature, timestamp, nonce):
        return Response(content="invalid signature", status_code=403)
    return Response(content=echostr, media_type="text/plain")


@router.post("", summary="接收用户消息", response_class=Response)
async def receive(request: Request) -> Response:
    """接收文本 / 图片消息，返回 XML 回复。"""
    body = await request.body()
    msg = wechat_xml.parse_message(body)
    logger.info("收到消息 from=%s type=%s", msg.get("openid"), msg.get("type"))
    reply_xml = await agent.handle(msg)
    return Response(content=reply_xml, media_type="application/xml")
