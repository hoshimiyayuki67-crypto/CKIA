from datetime import date

from campus_assistant.intelligence.retriever import retrieve
from campus_assistant.repositories.knowledge import KnowledgeRepository
from campus_assistant.schemas.chat import ActionCard, ChatRequest, ChatResponse
from campus_assistant.schemas.knowledge import UNKNOWN


def answer(
    request: ChatRequest, repository: KnowledgeRepository, today: date, demo_mode: bool = False
) -> ChatResponse:
    hits = retrieve(request, repository.eligible(today))
    if not hits:
        return ChatResponse(
            message="未查询到可核实的现行规定，请咨询学校相关职能部门。",
            demo_mode=demo_mode,
        )
    if len(hits) > 1:
        return ChatResponse(
            status="clarification",
            message="请明确想办理的事项：" + "、".join(
                dict.fromkeys(hit.fields.matter_name for hit in hits)
            ),
            demo_mode=demo_mode,
        )
    entry = hits[0]
    values = entry.fields.model_dump()
    for field in ("location", "office_hours", "channel", "contact"):
        values[field] = values[field] or UNKNOWN
    card = ActionCard(
        **values, sources=[entry.source], confidence=0.6,
    )
    # 暂无模型置信估计；保守固定值，不代表资格判断正确率。
    return ChatResponse(
        status="card", message="以下为已审核资料中的办事信息，请以职能部门答复为准。",
        card=card, sources=card.sources, demo_mode=demo_mode,
    )
