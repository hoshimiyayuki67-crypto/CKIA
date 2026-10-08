from campus_assistant.schemas.chat import ChatRequest, ChatResponse


def answer(request: ChatRequest) -> ChatResponse:
    # 开发骨架尚无检索依据，不能生成卡片或声称掌握校内规定。
    return ChatResponse(
        message="知识库尚未接入，暂无法核实相关规定。请咨询学校相关职能部门。"
    )
