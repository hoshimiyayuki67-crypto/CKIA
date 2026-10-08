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
    evidence = {reference(entry): entry.chunk_text[:1500] for entry in entries}
    evidence.update({source.id: source.snippet for source in results})
    if model:
        try:
            response.analysis = await model.analyze(request.question, school.name, evidence)
            cited = {key for claim in response.analysis for key in claim.references}
            response.local_evidence = {reference(entry): entry.source for entry in entries
                                       if reference(entry) in cited}
            response.ai_status = "used"
            response.ai_model = model.model
        except ModelUnavailable:
            response.ai_status = "unavailable"
    response.message += (
        "\n已检索所选院校官网，下面提供与本地资料一起筛选的证据。"
        "网络内容为搜索摘要，未经人工审核；请打开原文确认年份、适用对象和现行要求。"
        "如与本地资料不同，请向学校确认后办理。"
    )
    if not response.analysis:
        response.message += "\n暂未生成可核实的证据分析，可查看下方搜索结果。"
    return response
