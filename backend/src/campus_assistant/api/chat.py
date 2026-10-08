from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from campus_assistant.schemas.chat import ChatRequest, ChatResponse
from campus_assistant.services.answer import answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    return answer(
        payload, request.app.state.knowledge,
        datetime.now(timezone(timedelta(hours=8))).date(), request.app.state.demo_mode,
    )
