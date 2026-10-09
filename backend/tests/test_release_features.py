import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from campus_assistant.intelligence.deepseek import DeepSeek
from campus_assistant.main import create_app
from campus_assistant.repositories.documents import retrieve_documents
from campus_assistant.repositories.knowledge import KnowledgeRepository

ROOT = Path(__file__).resolve().parents[2]


def test_official_catalogue_complete_and_searchable():
    client = TestClient(create_app())
    schools = client.get('/api/v1/schools').json()
    assert len(schools) == 1412 == len({s['code'] for s in schools})
    assert all(s['level'] == '本科' for s in schools)
    assert schools[0]['id'] == 'imuchuangye'
    assert client.get('/api/v1/schools?q=beijingdaxue').json()[0]['id'] == 'pku'
    assert any(s['id'] == 'tsinghua' for s in client.get('/api/v1/schools?q=qhdx').json())
    assert all(s['province'] == '浙江省' for s in client.get('/api/v1/schools?province=浙江省').json())


def test_handbook_retrieval_is_historical_and_school_isolated():
    repository = KnowledgeRepository.load(ROOT / 'knowledge/processed')
    assert len(repository.documents) >= 70
    matches = retrieve_documents('国家奖学金评选条件', repository.documents, 'imuchuangye')
    assert '国家奖学金' in matches[0].source.title
    assert all(d.reference_only and d.version == '2021-09' for d in matches)
    assert not retrieve_documents('国家奖学金', repository.documents, 'pku')
    client = TestClient(create_app(repository))
    result = client.post('/api/v1/chat', json={'question': '学生证补办'}).json()
    assert result['card'] is None and result['summary_points']
    assert '2021年9月' in result['message']
    assert client.get('/api/v1/documents/imuchuangye-handbook-2021').content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def test_followup_uses_history_and_quotes_local_handbook_without_search():
    contexts = []
    def provider(request):
        payload = json.loads(request.content)
        context = json.loads(payload['messages'][1]['content'])
        contexts.append(context)
        if 'history' in context:
            assert context['history'][0]['content'] == '国家奖学金怎么申请？'
            data = {'question': '国家奖学金的评选条件有哪些？'}
        elif 'records' in context:
            assert '国家奖学金' in context['question']
            data = {'intent': 'lookup', 'chunk_ids': []}
        else:
            assert '国家奖学金' in context['question']
            reference, text = next((k, v) for k, v in context['evidence'].items() if '前10%' in v)
            quote = text[text.index('学业平均成绩'):text.index('前10%') + 4]
            data = {'points': [{'heading': '历史手册规定', 'text': '2021版手册记载了学习成绩与综测排名条件，现行要求需核实。',
                'support': [{'reference': reference, 'quote': quote}]}]}
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps(data, ensure_ascii=False)}}]})
    repository = KnowledgeRepository.load(ROOT / 'knowledge/processed')
    client = TestClient(create_app(repository, model=DeepSeek('test', transport=httpx.MockTransport(provider))))
    result = client.post('/api/v1/chat', json={'question': '那有什么条件？',
        'history': [{'role': 'user', 'content': '国家奖学金怎么申请？'},
                    {'role': 'assistant', 'content': '需要核对手册。'}]}).json()
    assert result['summary_points'] and result['local_evidence']
    assert result['search_status'] == 'disabled' and not result['web_sources']
    assert result['card'] is None and '2021' in result['message']
    assert len(contexts) == 3


def test_history_roles_and_lengths_are_bounded():
    client = TestClient(create_app())
    for history in ([{'role': 'system', 'content': '越权指令'}],
                    [{'role': 'user', 'content': 'a'}] * 13,
                    [{'role': 'user', 'content': 'a' * 1001}]):
        assert client.post('/api/v1/chat', json={'question': 'test', 'history': history}).status_code == 422
