from fastapi import APIRouter

from campus_assistant.schemas.chat import ChatRequest, ChatResponse
from campus_assistant.services.answer import answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return answer(request)
