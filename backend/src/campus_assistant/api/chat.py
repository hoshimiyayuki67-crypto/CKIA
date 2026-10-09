from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request

from campus_assistant.intelligence.deepseek import ModelUnavailable
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
            context_failed = False
            if payload.history and state.model:
                try:
                    payload = payload.model_copy(update={'question': await state.model.contextualize(payload)})
                except ModelUnavailable:
                    context_failed = True
            response = (await ai_answer(payload, state.knowledge, today, state.model, state.demo_mode)
                        if state.model else answer(payload, state.knowledge, today, state.demo_mode))
            response = await add_search(response, payload, state.knowledge, today,
                                       state.model, state.search, school)
            if context_failed:
                response.message += '\n暂时未能理解历史上下文，本次仅按当前问题查询；可补充完整事项后重试。'
            return response
        finally:
            state.call_limit.in_flight -= 1
    response = answer(
        payload, request.app.state.knowledge,
        today, request.app.state.demo_mode,
    )
    response.school_id = school.id
    return await add_search(response, payload, state.knowledge, today, None, state.search, school)


@router.get("/schools")
async def schools(q: str = Query(default='', max_length=100), province: str = Query(default='', max_length=30)):
    from dataclasses import asdict

    from campus_assistant.services.schools import SCHOOLS
    needle = q.strip().casefold().replace(' ', '')
    return [asdict(school) for school in SCHOOLS
            if (not province or school.province == province)
            and (not needle or any(needle in value.casefold().replace(' ', '')
                 for value in (school.name, school.pinyin, school.initials, school.city, school.code)))]
