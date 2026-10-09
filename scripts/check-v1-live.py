"""Explicit operator smoke: only synthetic queries, no production user messages."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

BASE = 'https://v4.yukifn.xyz:7010'


def get(path):
    with urlopen(BASE + path, timeout=20) as response:
        return response.read()


def ask(payload):
    request = Request(BASE + '/api/v1/chat', data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(request, timeout=110) as response:
        return json.load(response)


def main():
    health = json.loads(get('/health'))
    assert health['knowledge_status'] == 'loaded' and health['document_chunks'] == 73
    schools = json.loads(get('/api/v1/schools'))
    assert len(schools) == 1412
    assert json.loads(get('/api/v1/schools?' + urlencode({'q': 'qinghuadaxue'})))[0]['id'] == 'tsinghua'
    manifest = json.loads(Path('knowledge/official/handbook-2021.manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(get('/api/v1/documents/imuchuangye-handbook-2021')).hexdigest() == manifest['sha256']
    print('Public health, catalogue search and original document hash verified', flush=True)
    first = ask({'question': '学生证丢了怎么补办？'})
    assert first['summary_points'] and first['local_evidence'] and first['ai_status'] == 'used'
    assert '2021' in first['message'] and first['search_status'] == 'disabled'
    content = '\n'.join([first['message'], *[p['text'] for p in first['summary_points']]])[:1000]
    second = ask({'question': '那需要什么材料，在哪申请？', 'history': [
        {'role': 'user', 'content': '学生证丢了怎么补办？'}, {'role': 'assistant', 'content': content}]})
    assert second['summary_points'] and second['local_evidence'] and second['ai_status'] == 'used'
    assert all(s['doc_id'] == 'imuchuangye-handbook-2021' for s in second['local_evidence'].values())
    print('Real model handbook summary and contextual follow-up verified', flush=True)
    print(json.dumps({'followup': [p['text'] for p in second['summary_points']]}, ensure_ascii=False), flush=True)
    isolated = ask({'question': '学生证补办', 'school_id': 'pku'})
    assert not isolated['local_evidence'] and not isolated['card']
    print('Cross-school handbook isolation verified', flush=True)
    school = next(s for s in schools if s['name'] == '浙江大学')
    online = ask({'question': '本科生在读证明怎么办理？', 'school_id': school['id'],
        'school_name': '北京大学', 'school_domain': 'pku.edu.cn', 'search_enabled': True})
    assert online['search_status'] == 'used' and online['web_sources'] and online['summary_points']
    assert all((host := urlsplit(s['url']).hostname) == school['domain'] or host.endswith('.' + school['domain'])
               for s in online['web_sources'])
    assert not online['local_evidence']
    print('Exact selected-school official search and readable summary verified', flush=True)


if __name__ == '__main__':
    main()
