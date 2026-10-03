"""面向安卓客户端的 REST 接口数据结构。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """文字提问请求。"""

    session_id: str
    question: str = ""


class FeedbackRequest(BaseModel):
    """回答反馈请求。"""

    message_id: str
    useful: bool


class ChatResponse(BaseModel):
    """统一响应信封。

    type = card      -> data 为 ActionCard（办事卡片）
    type = refusal   -> data 为 Refusal（拒答 + 咨询渠道）
    type = text      -> data 为 {"text": "..."}（澄清追问 / 版本差异提示 / 降级文本）
    """

    type: Literal["card", "refusal", "text"]
    data: dict
