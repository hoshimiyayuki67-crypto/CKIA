from datetime import date

from campus_assistant.intelligence.deepseek import ModelUnavailable, reference
from campus_assistant.intelligence.retriever import retrieve
from campus_assistant.intelligence.web_search import SearchUnavailable
from campus_assistant.schemas.chat import ChatResponse


async def add_search(response: ChatResponse, request, repository, today: date, model, search, school):
    response.school_id = school.id
    if not request.search_enabled:
        return response
    try:
        results = await search.search(school, request.question, request.category)
    except SearchUnavailable:
        response.search_status = "unavailable"
        response.message += "\n联网搜索暂时不可用，以上仅为本地资料查询结果。"
        return response
    response.web_sources = results
    response.search_status = "used" if results else "empty"
    if not results:
        response.message += "\n未检索到所选院校官网的相关结果。"
        return response
    entries = [entry for entry in repository.eligible(today)
               if entry.school_id == school.id
               and (not request.category or entry.category == request.category)]
    ranked = retrieve(request, entries)
    entries = (ranked + [entry for entry in entries if entry not in ranked])[:8]
    evidence = {reference(entry): entry.chunk_text[:3000] for entry in entries}
    evidence.update({source.id: source.snippet[:6000] for source in results[:6]})
    if model:
        try:
            response.summary_points = await model.summarize(request.question, school.name, evidence)
            cited = {support.reference for point in response.summary_points for support in point.support}
            response.local_evidence = {reference(entry): entry.source for entry in entries
                                       if reference(entry) in cited}
            response.ai_status = "used"
            response.ai_model = model.model
            if response.summary_points and response.card is None:
                response.status = "clarification"
                response.message = "根据所选院校资料，为你整理如下："
        except ModelUnavailable:
            response.ai_status = "unavailable"
    response.message += (
        "\n官网资料由 AI 整理，未经人工审核；办理前请核对原文年份与适用对象。"
    )
    if not response.summary_points:
        response.message += "\n暂未获得足够依据生成总结，可展开来源查看相关资料。"
    # Full pages are model context, not a wall of text shipped to the conversation.
    response.web_sources = [source.model_copy(update={"snippet": source.snippet[:800]})
                            for source in results]
    return response
