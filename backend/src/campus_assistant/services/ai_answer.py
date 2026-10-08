import time
from collections import OrderedDict, deque
from datetime import date

from campus_assistant.intelligence.deepseek import DeepSeek, ModelUnavailable, reference
from campus_assistant.intelligence.retriever import retrieve
from campus_assistant.repositories.knowledge import KnowledgeRepository
from campus_assistant.schemas.chat import ChatRequest, ChatResponse
from campus_assistant.services.answer import answer, answer_from_hits


class CallLimit:
    """Single-worker limits: 6 calls/IP/minute, 30 total/minute, 2 in flight."""

    def __init__(self):
        self.total = deque()
        self.clients = OrderedDict()
        self.in_flight = 0

    def enter(self, client: str) -> bool:
        now = time.monotonic()
        while self.total and self.total[0] <= now - 60:
            self.total.popleft()
        calls = self.clients.setdefault(client, deque())
        self.clients.move_to_end(client)
        while calls and calls[0] <= now - 60:
            calls.popleft()
        if len(self.clients) > 1024:
            self.clients.popitem(last=False)
        if self.in_flight >= 2 or len(self.total) >= 30 or len(calls) >= 6:
            return False
        self.total.append(now)
        calls.append(now)
        self.in_flight += 1
        return True


async def ai_answer(
    request: ChatRequest, repository: KnowledgeRepository, today: date,
    model: DeepSeek, demo_mode: bool = False,
) -> ChatResponse:
    eligible = [entry for entry in repository.eligible(today)
                if entry.school_id == request.school_id
                and (not request.category or entry.category == request.category)]
    # First bounded candidate pass; vector retrieval remains a later task.
    ranked = retrieve(request, eligible)
    candidates = (ranked + [entry for entry in eligible if entry not in ranked])[:8]
    try:
        selected = await model.select(request, candidates)
    except ModelUnavailable:
        response = answer(request, repository, today, demo_mode)
        response.ai_status = "unavailable"
        if response.status == "refusal":
            response.message = "AI 服务暂时不可用，未查到可核实的现行规定，请咨询相关职能部门。"
        return response
    if selected.intent == "greeting":
        response = ChatResponse(
            status="clarification", demo_mode=demo_mode,
            message="你好，我是校园万事通助手。你想了解哪项校园事务？我会根据已审核资料查询，"
                    "没有依据的规定会明确告知。",
        )
    else:
        hits = [entry for entry in candidates if reference(entry) in selected.chunk_ids]
        response = answer_from_hits(hits, demo_mode)
    response.ai_status = "used"
    response.ai_model = model.model
    return response
