from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

from campus_assistant.schemas.chat import ChatRequest, ChatResponse
from campus_assistant.services.ai_answer import ai_answer
from campus_assistant.services.answer import answer
from campus_assistant.services.schools import resolve_school
from campus_assistant.services.search_answer import add_search

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    state = request.app.state
    today = datetime.now(timezone(timedelta(hours=8))).date()
    try:
        school = resolve_school(payload)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    if state.model or payload.search_enabled:
        peer = request.client.host if request.client else "unknown"
        if not state.call_limit.enter(peer):
            raise HTTPException(429, "AI 请求繁忙，请稍后重试", headers={"Retry-After": "60"})
        try:
            response = (await ai_answer(payload, state.knowledge, today, state.model, state.demo_mode)
                        if state.model else answer(payload, state.knowledge, today, state.demo_mode))
            return await add_search(response, payload, state.knowledge, today,
                                    state.model, state.search, school)
        finally:
            state.call_limit.in_flight -= 1
    response = answer(
        payload, request.app.state.knowledge,
        today, request.app.state.demo_mode,
    )
    response.school_id = school.id
    return response


@router.get("/schools")
async def schools():
    from dataclasses import asdict

    from campus_assistant.services.schools import SCHOOLS
    return [asdict(school) for school in SCHOOLS]
