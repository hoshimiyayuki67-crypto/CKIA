import sqlite3

from fastapi.testclient import TestClient

from campus_assistant.main import create_app
from campus_assistant.repositories.accounts import Accounts


def client(tmp_path):
    return TestClient(create_app(accounts=Accounts(tmp_path / 'accounts.sqlite3')))


def register(api, name='alice'):
    response = api.post('/api/v1/auth/register', json={'username': name, 'password': 'safe-password-123'})
    assert response.status_code == 200
    return response.json()


def headers(result):
    return {'Authorization': 'Bearer ' + result['token']}


def session(revision=0):
    return {'revision': revision, 'data': {'title': '查询成绩单', 'school': {
        'id': 'pku', 'name': '北京大学', 'domain': 'pku.edu.cn'}, 'category': None,
        'updated_at': '2026-10-09T01:00:00', 'messages': [{'user': True, 'message': '成绩单'}]}}


def test_account_password_storage_login_revocation_and_deletion(tmp_path):
    api = client(tmp_path)
    result = register(api)
    assert api.get('/api/v1/auth/me', headers=headers(result)).json()['username'] == 'alice'
    assert api.post('/api/v1/auth/login', json={'username': 'ALICE', 'password': 'wrong-password'}).status_code == 401
    login = api.post('/api/v1/auth/login', json={'username': 'ALICE', 'password': 'safe-password-123'}).json()
    assert login['user'] == result['user'] and login['token'] != result['token']
    with sqlite3.connect(tmp_path / 'accounts.sqlite3') as db:
        assert db.execute('SELECT password FROM users').fetchone()[0] != 'safe-password-123'
        assert result['token'] not in str(db.execute('SELECT * FROM tokens').fetchall())
    api.post('/api/v1/auth/logout', headers=headers(result))
    assert api.get('/api/v1/auth/me', headers=headers(result)).status_code == 401
    api.put('/api/v1/sessions/s1', json=session(), headers=headers(login))
    assert api.request('DELETE', '/api/v1/auth/account', json={'password': 'wrong-password'}, headers=headers(login)).status_code == 401
    assert api.request('DELETE', '/api/v1/auth/account', json={'password': 'safe-password-123'}, headers=headers(login)).status_code == 200
    assert api.get('/api/v1/sessions', headers=headers(login)).status_code == 401
    with sqlite3.connect(tmp_path / 'accounts.sqlite3') as db:
        assert db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0


def test_cloud_isolation_revision_conflict_tombstone_and_restart(tmp_path):
    api = client(tmp_path)
    alice, bob = register(api), register(api, 'bob')
    assert api.put('/api/v1/sessions/s1', json=session(), headers=headers(alice)).json()['revision'] == 1
    assert api.get('/api/v1/sessions', headers=headers(bob)).json()['sessions'] == []
    assert api.delete('/api/v1/sessions/s1?revision=1', headers=headers(bob)).status_code == 409
    assert api.put('/api/v1/sessions/s1', json=session(), headers=headers(alice)).status_code == 409
    assert api.put('/api/v1/sessions/s1', json=session(1), headers=headers(alice)).json()['revision'] == 2
    restarted = client(tmp_path)
    rows = restarted.get('/api/v1/sessions', headers=headers(alice)).json()['sessions']
    assert rows[0]['data']['title'] == '查询成绩单' and rows[0]['revision'] == 2
    assert restarted.delete('/api/v1/sessions/s1?revision=2', headers=headers(alice)).status_code == 200
    assert restarted.get('/api/v1/sessions', headers=headers(alice)).json()['sessions'][0]['deleted']
    assert restarted.put('/api/v1/sessions/s1', json=session(3), headers=headers(alice)).status_code == 409


def test_validation_payload_limit_and_auth_rate_limit(tmp_path):
    api = client(tmp_path)
    assert api.get('/api/v1/sessions').status_code == 401
    assert api.post('/api/v1/auth/register', json={'username': '../bad', 'password': 'short'}).status_code == 422
    assert api.post('/api/v1/auth/login', content='x' * 5000).status_code == 413
    result = register(api)
    oversized = session()
    oversized['data']['messages'] = [{'message': 'x' * 220000}]
    assert api.put('/api/v1/sessions/huge', json=oversized, headers=headers(result)).status_code == 413
    for _ in range(10):
        response = api.post('/api/v1/auth/login', json={'username': 'missing', 'password': 'wrong-password'})
    assert response.status_code == 429


def test_cloud_active_session_quota(tmp_path):
    api = client(tmp_path)
    result = register(api)
    for i in range(50):
        assert api.put(f'/api/v1/sessions/s{i}', json=session(), headers=headers(result)).status_code == 200
    assert api.put('/api/v1/sessions/full', json=session(), headers=headers(result)).status_code == 409
    api.delete('/api/v1/sessions/s0?revision=1', headers=headers(result))
    assert api.put('/api/v1/sessions/available', json=session(), headers=headers(result)).status_code == 200
