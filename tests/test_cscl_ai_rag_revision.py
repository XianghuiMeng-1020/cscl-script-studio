"""Tests for CSCL AI, RAG, and Revision features"""
import pytest
import json
import os
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLScene, CSCLScriptRevision
from datetime import datetime


@pytest.fixture(autouse=True)
def set_mock_provider():
    """Set LLM_PROVIDER to mock for all tests"""
    os.environ['LLM_PROVIDER'] = 'mock'
    yield
    # Cleanup if needed


def test_teacher_generate_ai_mock_provider(client, app, seed_users):
    """Test 1: teacher generate-ai -> 200 (mock provider)"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    assert create_resp.status_code == 201
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Generate AI plan
    resp = client.post(f'/api/cscl/scripts/{script_id}/generate-ai')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'plan' in data
    assert 'provider' in data
    assert data['provider'] == 'mock'


def test_teacher_regenerate_scene(client, app, seed_users):
    """Test 2: teacher regenerate-scene -> 200"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script with template
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60,
            'generate_template': True
        }
    )
    assert create_resp.status_code == 201
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Get script to find scene_id
    get_resp = client.get(f'/api/cscl/scripts/{script_id}')
    script_data = json.loads(get_resp.data)['script']
    scene_id = script_data['scenes'][0]['id'] if script_data['scenes'] else None
    
    assert scene_id is not None
    
    # Regenerate scene
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/regenerate-scene',
        json={
            'scene_id': scene_id,
            'instruction': 'Make it more engaging'
        }
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'scene' in data


def test_revisions_timeline(client, app, seed_users):
    """Test 3: revisions timeline readable -> 200 and count increases"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script (creates revision)
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    assert create_resp.status_code == 201
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Get revisions (should have 1)
    resp = client.get(f'/api/cscl/scripts/{script_id}/revisions')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    initial_count = len(data['revisions'])
    assert initial_count >= 1
    
    # Update script (creates another revision)
    update_resp = client.put(
        f'/api/cscl/scripts/{script_id}',
        json={'title': 'Updated Script'}
    )
    assert update_resp.status_code == 200
    
    # Get revisions again (should have more)
    resp = client.get(f'/api/cscl/scripts/{script_id}/revisions')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data['revisions']) > initial_count


def test_student_generate_ai_forbidden(client, app, seed_users):
    """Test 4: student generate-ai -> 403"""
    # Login as student
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'S001', 'password': 'student123'}
    )
    assert login_resp.status_code == 200
    
    # Try to generate AI
    resp = client.post('/api/cscl/scripts/any-id/generate-ai')
    assert resp.status_code == 403
    data = json.loads(resp.data)
    assert 'error' in data


def test_provider_missing_key_error(client, app, seed_users):
    """Test 5: provider missing key returns explainable error (not 500)"""
    # Set provider to openai without key
    original_provider = os.environ.get('LLM_PROVIDER')
    os.environ['LLM_PROVIDER'] = 'openai'
    
    # Reload config and provider module
    import importlib
    import app.config
    import app.services.cscl_llm_provider
    importlib.reload(app.config)
    importlib.reload(app.services.cscl_llm_provider)
    
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Try to generate AI (should return error, not 500)
    resp = client.post(f'/api/cscl/scripts/{script_id}/generate-ai')
    assert resp.status_code in [400, 503]  # Should be 400 or 503, not 500
    data = json.loads(resp.data)
    assert 'error' in data
    assert 'code' in data or 'provider' in data
    
    # Restore original provider
    if original_provider:
        os.environ['LLM_PROVIDER'] = original_provider
    else:
        os.environ.pop('LLM_PROVIDER', None)


def test_rag_fallback_no_course_docs(client, app, seed_users):
    """Test 6: RAG fallback normal when no course docs (empty chunks but can generate)"""
    # Login as teacher
    login_resp = client.post(
        '/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    assert login_resp.status_code == 200
    
    # Create script
    create_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(create_resp.data)['script']['id']
    
    # Generate AI (should work even without course docs)
    resp = client.post(f'/api/cscl/scripts/{script_id}/generate-ai')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'retrieved_chunks' in data
    # Chunks can be empty, but generation should still work
    assert isinstance(data['retrieved_chunks'], list)
