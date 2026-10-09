from datetime import date

from campus_assistant.intelligence.deepseek import ModelUnavailable, reference
from campus_assistant.intelligence.retriever import retrieve
from campus_assistant.intelligence.web_search import SearchUnavailable
from campus_assistant.repositories.documents import retrieve_documents
from campus_assistant.schemas.chat import ChatResponse


async def add_search(response: ChatResponse, request, repository, today: date, model, search, school):
    response.school_id = school.id
    documents = retrieve_documents(request.question, repository.documents, school.id)
    results = []
    if request.search_enabled:
        try:
            results = await search.search(school, request.question, request.category)
            response.search_status = 'used' if results else 'empty'
        except SearchUnavailable:
            response.search_status = 'unavailable'
            response.message += ('\n暂未确认所选院校官网，可在院校选择中指定官网域名；以下仅按本地资料分析。'
                if not school.domain else '\n联网搜索暂时不可用，以下仅按本地资料分析。')
    response.web_sources = results
    if request.search_enabled and not results and response.search_status != 'unavailable':
        response.message += "\n未检索到所选院校官网的相关结果。"
    if not results and not documents:
        return response
    entries = [entry for entry in repository.eligible(today)
               if entry.school_id == school.id
               and (not request.category or entry.category == request.category)]
    ranked = retrieve(request, entries)
    entries = (ranked + [entry for entry in entries if entry not in ranked])[:8]
    evidence = {reference(entry): entry.chunk_text[:3000] for entry in entries}
    evidence.update({reference(document): f'【{document.version}历史版：{document.source.title}】\n{document.text}'
                     for document in documents})
    evidence.update({source.id: source.snippet[:6000] for source in results[:6]})
    if model:
        try:
            response.summary_points = await model.summarize(request.question, school.name, evidence)
            cited = {support.reference for point in response.summary_points for support in point.support}
            response.local_evidence = {reference(entry): entry.source for entry in entries
                                       if reference(entry) in cited}
            response.local_evidence.update({reference(d): d.source for d in documents if reference(d) in cited})
            response.ai_status = "used"
            response.ai_model = model.model
            if response.summary_points and response.card is None:
                response.status = "clarification"
                response.message = "根据所选院校资料，为你整理如下："
        except ModelUnavailable:
            response.ai_status = "unavailable"
    if results:
        response.message += '\n官网资料由 AI 整理，未经人工审核；办理前请核对原文年份与适用对象。'
    if documents:
        response.message += '\n本地学生手册为2021年9月历史版本，仅供参考；现行要求请向学校核实。'
    if not response.summary_points:
        if documents and (not model or response.ai_status == 'unavailable'):
            from campus_assistant.schemas.chat import SummaryPoint, SupportQuote
            for document in documents[:3]:
                quote = document.text[:220]
                response.summary_points.append(SummaryPoint(heading='历史手册原文', text=quote,
                    support=[SupportQuote(reference=reference(document), quote=quote)]))
                response.local_evidence[reference(document)] = document.source
            response.status = 'clarification' if response.card is None else response.status
        else:
            response.message += "\n暂未获得足够依据生成总结，可展开来源查看相关资料。"
    # Full pages are model context, not a wall of text shipped to the conversation.
    response.web_sources = [source.model_copy(update={"snippet": source.snippet[:800]})
                            for source in results]
    return response
