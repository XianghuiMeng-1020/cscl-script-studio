"""C1: Idempotency cache tests (in-memory and behaviour)."""
import pytest
import json
from unittest.mock import patch
from app.services.pipeline.idempotency import (
    get_cached_run_for_key,
    set_cached_run_for_key,
)


@pytest.fixture
def app_with_idempotency(app):
    """Ensure REDIS_URL is unset so we use in-memory."""
    app.config['REDIS_URL'] = ''
    return app


def test_idempotency_set_then_get_returns_same_run_id(app_with_idempotency):
    """Set then get returns the same run_id within TTL."""
    with app_with_idempotency.app_context():
        set_cached_run_for_key('script-1', 'key-alpha', 'run-001')
        out = get_cached_run_for_key('script-1', 'key-alpha')
        assert out == 'run-001'


def test_idempotency_different_key_misses(app_with_idempotency):
    """Different idempotency key has no cache hit."""
    with app_with_idempotency.app_context():
        set_cached_run_for_key('script-1', 'key-alpha', 'run-001')
        assert get_cached_run_for_key('script-1', 'key-beta') is None


def test_idempotency_different_script_misses(app_with_idempotency):
    """Different script_id has no cache hit."""
    with app_with_idempotency.app_context():
        set_cached_run_for_key('script-1', 'key-alpha', 'run-001')
        assert get_cached_run_for_key('script-2', 'key-alpha') is None


def test_idempotency_empty_key_ignored(app_with_idempotency):
    """Empty idempotency key does not store or return."""
    with app_with_idempotency.app_context():
        set_cached_run_for_key('script-1', '', 'run-001')
        assert get_cached_run_for_key('script-1', '') is None


def test_pipeline_run_idempotent_same_key_returns_same_run_id(client, app, seed_users):
    """C1: Two POSTs with same Idempotency-Key return same run_id (no duplicate run)."""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Idem Test',
            'topic': 'T',
            'course_id': 'default-course',
            'task_type': 'structured_debate',
            'duration_minutes': 60,
        },
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    spec = {
        'course_context': {
            'subject': 'S',
            'topic': 'T',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Desc.',
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'O',
            'collaboration_form': 'group',
            'requirements_text': 'Req.',
        },
    }
    idem_key = 'test-idem-key-12345'
    headers = {'Content-Type': 'application/json', 'Idempotency-Key': idem_key}
    body = json.dumps({'spec': spec, 'idempotency_key': idem_key})

    r1 = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        data=body,
        headers=headers,
        content_type='application/json',
    )
    assert r1.status_code == 200
    d1 = json.loads(r1.data)
    run_id_1 = d1.get('run_id')
    assert run_id_1

    r2 = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        data=body,
        headers=headers,
        content_type='application/json',
    )
    assert r2.status_code == 200
    d2 = json.loads(r2.data)
    run_id_2 = d2.get('run_id')
    assert run_id_2 == run_id_1
    assert d2.get('idempotent_reuse') is True


def test_idempotency_repeated_same_key_returns_same_run_id(client, app, seed_users):
    """C1: 15 sequential POSTs with same Idempotency-Key all return the same run_id (no duplicate runs)."""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Repeat Idem',
            'topic': 'T',
            'course_id': 'default-course',
            'task_type': 'structured_debate',
            'duration_minutes': 60,
        },
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    spec = {
        'course_context': {
            'subject': 'S',
            'topic': 'T',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'D.',
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'O',
            'collaboration_form': 'group',
            'requirements_text': 'R.',
        },
    }
    idem_key = 'repeat-key-15'
    headers = {'Content-Type': 'application/json', 'Idempotency-Key': idem_key}
    body = json.dumps({'spec': spec, 'idempotency_key': idem_key})
    run_ids = []
    for _ in range(15):
        r = client.post(
            f'/api/cscl/scripts/{script_id}/pipeline/run',
            data=body,
            headers=headers,
            content_type='application/json',
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        run_ids.append(data.get('run_id'))
    assert len(set(run_ids)) == 1, 'All 15 requests with same key must return the same run_id'
