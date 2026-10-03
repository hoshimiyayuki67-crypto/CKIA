"""微信消息 XML 解析与回复构造（接入层工具）。"""
from __future__ import annotations

import time
from xml.etree import ElementTree


def parse_message(body: bytes) -> dict:
    """解析微信推送的 XML 消息，返回统一结构。

    返回：{"openid": str, "type": "text"|"image", "text": str, "image": bytes|None}
    """
    root = ElementTree.fromstring(body)
    openid = root.findtext("FromUserName", default="")
    msg_type = root.findtext("MsgType", default="text")

    if msg_type == "image":
        # TODO 通过 PicUrl 下载图片字节，作为 image 传入多模态链路
        return {"openid": openid, "type": "image", "text": "", "image": None}

    content = (root.findtext("Content", default="") or "").strip()
    return {"openid": openid, "type": "text", "text": content, "image": None}


def build_text_reply(openid: str, content: str) -> str:
    """构造文本回复 XML。"""
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{openid}]]></ToUserName>"
        "<FromUserName><![CDATA[campus-agent]]></FromUserName>"
        f"<CreateTime>{int(time.time())}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{content}]]></Content>"
        "</xml>"
    )
