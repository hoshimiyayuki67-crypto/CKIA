import json

import httpx
from fastapi.testclient import TestClient

from campus_assistant.intelligence.deepseek import DeepSeek
from campus_assistant.intelligence.web_search import TavilySearch
from campus_assistant.main import create_app


def test_full_text_traversal_domain_filter_cache_and_summary():
    calls, contexts = [], []

    def search(request):
        data = json.loads(request.content)
        calls.append(request.url.path)
        if request.url.path == '/search':
            assert data['search_depth'] == 'advanced' and data['include_raw_content'] == 'markdown'
            return httpx.Response(200, json={'results': [
                {'title': '成绩单', 'url': 'https://pku.edu.cn/service', 'content': '办理成绩单'}]})
        if request.url.path == '/extract':
            assert data['urls'] == ['https://pku.edu.cn/service']
            return httpx.Response(200, json={'results': [
                {'url': 'https://pku.edu.cn/service', 'raw_content': '在校生可在自助打印机打印成绩单。'}]})
        assert request.url.path == '/crawl'
        assert not data['allow_external'] and data['max_depth'] == 2 and data['limit'] == 3
        return httpx.Response(200, json={'results': [
            {'url': 'https://dean.pku.edu.cn/detail', 'raw_content': '1998届之前毕业生需注册邮箱账户。'},
            {'url': 'https://pku.edu.cn.evil.test/x', 'raw_content': '错误信息'}]})

    def model(request):
        context = json.loads(json.loads(request.content)['messages'][1]['content'])
        if 'records' in context:
            result = {'intent': 'lookup', 'chunk_ids': []}
        else:
            contexts.append(context)
            result = {'points': [{'heading': '办理方式', 'text': '在校生可以使用自助打印机办理成绩单。',
                'support': [{'reference': 'web-1', 'quote': '在校生可在自助打印机打印成绩单。'}]}]}
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps(result, ensure_ascii=False)}}]})

    api = TestClient(create_app(search=TavilySearch('key', httpx.MockTransport(search)),
                              model=DeepSeek('key', transport=httpx.MockTransport(model))))
    query = {'question': '成绩单办理', 'school_id': 'pku', 'search_enabled': True}
    response = api.post('/api/v1/chat', json=query).json()
    assert response['status'] == 'clarification' and response['summary_points']
    assert response['web_sources'][0]['content_kind'] == 'page'
    assert len(response['web_sources']) == 2 and len(contexts[0]['evidence']) == 2
    assert '自助打印机' in contexts[0]['evidence']['web-1']
    assert set(calls) == {'/search', '/extract', '/crawl'}
    api.post('/api/v1/chat', json=query)
    assert len(calls) == 3  # Repeated school/question uses bounded ten-minute cache.


def test_enrichment_failure_retains_search_and_unsupported_summary_is_rejected():
    def search(request):
        if request.url.path != '/search':
            return httpx.Response(503)
        return httpx.Response(200, json={'results': [
            {'title': '通知', 'url': 'https://pku.edu.cn/x', 'content': '提交学生证'}]})

    def model(request):
        context = json.loads(json.loads(request.content)['messages'][1]['content'])
        result = ({'intent': 'lookup', 'chunk_ids': []} if 'records' in context else
                  {'points': [{'heading': '材料', 'text': '免交材料',
                               'support': [{'reference': 'web-1', 'quote': '无需材料'}]}]})
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
                                                     'message': {'content': json.dumps(result)}}]})
    api = TestClient(create_app(search=TavilySearch('key', httpx.MockTransport(search)),
                              model=DeepSeek('key', transport=httpx.MockTransport(model))))
    response = api.post('/api/v1/chat', json={'question': '材料', 'school_id': 'pku',
                                             'search_enabled': True}).json()
    assert response['search_status'] == 'used' and response['web_sources']
    assert not response['summary_points'] and response['ai_status'] == 'unavailable'
