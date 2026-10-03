"""面向安卓 APP 的 REST JSON 接口（接入层）。

与微信端共用 app.core.agent.process 处理链路，仅输出形式为 JSON。
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.core import agent, feedback, session
from app.schemas.api import ChatRequest, ChatResponse, FeedbackRequest
from app.schemas.card import ActionCard, Refusal

router = APIRouter(prefix="/api/v1", tags=["安卓端"])


def _envelope(result) -> ChatResponse:
    """将核心链路结果包装为统一响应信封。"""
    if isinstance(result, ActionCard):
        return ChatResponse(type="card", data=result.model_dump(mode="json"))
    if isinstance(result, Refusal):
        return ChatResponse(type="refusal", data=result.model_dump(mode="json"))
    return ChatResponse(type="text", data={"text": str(result)})


@router.post("/chat", response_model=ChatResponse, summary="文字提问")
async def chat(req: ChatRequest) -> ChatResponse:
    session_hash = session.session_store.hash_of(req.session_id)
    result = await agent.process(session_hash, req.question, None)
    return _envelope(result)


@router.post("/chat/image", response_model=ChatResponse, summary="截图提问（以图问图）")
async def chat_image(
    session_id: str = Form(...),
    question: str = Form(""),
    file: UploadFile = File(...),
) -> ChatResponse:
    session_hash = session.session_store.hash_of(session_id)
    image = await file.read()
    result = await agent.process(session_hash, question, image)
    return _envelope(result)


@router.post("/feedback", summary="回答反馈")
async def submit_feedback(req: FeedbackRequest) -> dict:
    feedback.record(req.message_id, req.useful)
    return {"ok": True}
