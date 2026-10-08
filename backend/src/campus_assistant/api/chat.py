from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

from campus_assistant.schemas.chat import ChatRequest, ChatResponse
from campus_assistant.services.ai_answer import ai_answer
from campus_assistant.services.answer import answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    state = request.app.state
    today = datetime.now(timezone(timedelta(hours=8))).date()
    if state.model:
        peer = request.client.host if request.client else "unknown"
        if not state.call_limit.enter(peer):
            raise HTTPException(429, "AI 请求繁忙，请稍后重试", headers={"Retry-After": "60"})
        try:
            return await ai_answer(payload, state.knowledge, today, state.model, state.demo_mode)
        finally:
            state.call_limit.in_flight -= 1
    return answer(
        payload, request.app.state.knowledge,
        today, request.app.state.demo_mode,
    )
