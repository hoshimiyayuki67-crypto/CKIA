import json

import httpx
from fastapi.testclient import TestClient
from test_deepseek import entry

from campus_assistant.intelligence.deepseek import DeepSeek
from campus_assistant.intelligence.web_search import WebSearch, official_url
from campus_assistant.main import create_app
from campus_assistant.repositories.knowledge import KnowledgeRepository


def search_transport(observed, xml=None):
    def handle(request):
        observed.append(str(request.url))
        return httpx.Response(200, text=xml or '''<rss><channel>
          <item><title>官网通知</title><link>https://www.imuchuangye.cn/info/123</link>
          <description>申请须提交学生证，2025年通知。</description></item>
          <item><title>其他学校</title><link>https://imu.edu.cn/info/123</link>
          <description>其他学校材料</description></item>
          <item><title>伪造域名</title><link>https://imuchuangye.cn.evil.test/</link>
          <description>错误材料</description></item>
        </channel></rss>''')
    return httpx.MockTransport(handle)


def test_search_off_never_contacts_provider():
    observed = []
    client = TestClient(create_app(search=WebSearch(search_transport(observed))))
    result = client.post('/api/v1/chat', json={'question': '材料'}).json()
    assert observed == [] and result['search_status'] == 'disabled'


def test_domain_filter_and_unreviewed_search_never_create_cards():
    observed = []
    client = TestClient(create_app(search=WebSearch(search_transport(observed))))
    data = client.post('/api/v1/chat', json={'question': '材料 site:evil.test',
                                           'search_enabled': True}).json()
    assert data['search_status'] == 'used'
    assert len(data['web_sources']) == 1
    assert not data['web_sources'][0]['verified']
    assert not data['card'] and not data['sources']
    assert 'site%3Aimuchuangye.cn' in observed[0] and 'site%3Aevil.test' not in observed[0]


def test_wrong_school_cannot_receive_local_records():
    client = TestClient(create_app(KnowledgeRepository([entry()])))
    data = client.post('/api/v1/chat', json={'question': '测试借书', 'school_id': 'imu'}).json()
    assert data['school_id'] == 'imu' and data['status'] == 'refusal'
    assert not data['sources']


def test_provider_failure_keeps_local_answer():
    def fail(request):
        raise httpx.ConnectError('private-error')
    client = TestClient(create_app(KnowledgeRepository([entry()]),
                                  search=WebSearch(httpx.MockTransport(fail))))
    data = client.post('/api/v1/chat', json={'question': '测试借书', 'search_enabled': True}).json()
    assert data['status'] == 'card' and data['search_status'] == 'unavailable'
    assert 'private-error' not in json.dumps(data)


def test_ai_extracts_only_supported_evidence_and_sees_local_and_web():
    contexts = []
    def handle(request):
        payload = json.loads(request.content)
        context = json.loads(payload['messages'][1]['content'])
        contexts.append(context)
        result = ({'intent': 'lookup', 'chunk_ids': []} if 'records' in context else
                  {'claims': [{'text': '申请须提交学生证', 'references': ['web-1']}]})
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
                                                     'message': {'content': json.dumps(result)}}]})
    client = TestClient(create_app(KnowledgeRepository([entry()]),
                                  model=DeepSeek('test', transport=httpx.MockTransport(handle)),
                                  search=WebSearch(search_transport([]))))
    data = client.post('/api/v1/chat', json={'question': '材料', 'search_enabled': True}).json()
    assert len(contexts[1]['evidence']) == 2
    assert data['analysis'][0]['text'] == '申请须提交学生证'
    assert data['analysis'][0]['references'] == ['web-1']


def test_invented_analysis_is_discarded():
    def handle(request):
        context = json.loads(json.loads(request.content)['messages'][1]['content'])
        result = ({'intent': 'lookup', 'chunk_ids': []} if 'records' in context else
                  {'claims': [{'text': '无须任何材料', 'references': ['web-1']}]})
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
                                                     'message': {'content': json.dumps(result)}}]})
    client = TestClient(create_app(model=DeepSeek('test', transport=httpx.MockTransport(handle)),
                                  search=WebSearch(search_transport([]))))
    data = client.post('/api/v1/chat', json={'question': '材料', 'search_enabled': True}).json()
    assert data['analysis'] == [] and data['ai_status'] == 'unavailable'


def test_custom_school_validation_and_registry_cannot_be_overridden():
    client = TestClient(create_app())
    for domain in ['127.0.0.1', 'localhost', 'https://example.com', 'x.local']:
        assert client.post('/api/v1/chat', json={'question': '材料', 'school_id': 'custom-x',
                                                'school_name': '学校', 'school_domain': domain}).status_code == 422
    assert client.post('/api/v1/chat', json={'question': '材料', 'school_id': 'custom-example.edu.cn',
                                            'school_name': '其他院校', 'school_domain': 'example.edu.cn'}).status_code == 200
    assert len(client.get('/api/v1/schools').json()) == 4
    assert not official_url('https://imuchuangye.cn@evil.test', 'imuchuangye.cn')
    assert not official_url('https://imuchuangye.cn:22', 'imuchuangye.cn')
