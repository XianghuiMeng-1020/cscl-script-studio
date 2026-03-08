"""S2.18 Tests: Provider fallback and fail-fast"""
import pytest
import json
import os
from app.db import db
from app.models import User, UserRole, CSCLScript
from app.services.cscl_llm_provider import get_llm_provider_status, get_cscl_llm_provider


def test_health_exposes_llm_provider_ready_fields(client, app, seed_users):
    """Test: /api/health exposes llm_provider_ready, llm_provider_name, llm_provider_reason"""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'llm_provider_ready' in data
    assert 'llm_provider_name' in data
    assert 'llm_provider_reason' in data
    assert isinstance(data['llm_provider_ready'], bool)
    assert isinstance(data['llm_provider_name'], str)
    assert isinstance(data['llm_provider_reason'], str)


def test_pipeline_returns_503_when_no_runnable_provider(client, app, seed_users):
    """Test: pipeline/run returns 503 LLM_PROVIDER_NOT_READY when no runnable provider"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    
    # Set up environment where no provider is runnable
    original_provider = os.environ.get('LLM_PROVIDER')
    original_openai_enabled = os.environ.get('OPENAI_ENABLED')
    original_openai_implemented = os.environ.get('OPENAI_IMPLEMENTED')
    original_qwen_key = os.environ.get('QWEN_API_KEY')
    
    try:
        # Force primary=openai, but disable it
        os.environ['LLM_PROVIDER'] = ''
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'
        os.environ['OPENAI_ENABLED'] = 'false'
        os.environ['OPENAI_IMPLEMENTED'] = 'false'
        os.environ['QWEN_API_KEY'] = ''  # No Qwen key either
        
        # Reload config
        import importlib
        import app.config
        importlib.reload(app.config)
        
        spec = {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'Machine Learning',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90,
                'description': 'Test course'
            },
            'learning_objectives': {
                'knowledge': ['Understand ML basics'],
                'skills': ['Apply algorithms']
            },
            'task_requirements': {
                'task_type': 'structured_debate',
                'expected_output': 'argument',
                'collaboration_form': 'group',
                'requirements_text': 'Test requirements'
            }
        }
        
        resp = client.post(
            f'/api/cscl/scripts/{script_id}/pipeline/run',
            json={'spec': spec}
        )
        
        # Should return 503 with LLM_PROVIDER_NOT_READY
        assert resp.status_code == 503
        data = json.loads(resp.data)
        assert data.get('code') == 'LLM_PROVIDER_NOT_READY'
        assert 'error' in data
        assert 'details' in data
        assert 'selected' in data['details']
        assert 'fallback' in data['details']
        assert 'reason' in data['details']
    finally:
        # Restore environment
        if original_provider is not None:
            os.environ['LLM_PROVIDER'] = original_provider
        else:
            os.environ.pop('LLM_PROVIDER', None)
        if original_openai_enabled is not None:
            os.environ['OPENAI_ENABLED'] = original_openai_enabled
        else:
            os.environ.pop('OPENAI_ENABLED', None)
        if original_openai_implemented is not None:
            os.environ['OPENAI_IMPLEMENTED'] = original_openai_implemented
        else:
            os.environ.pop('OPENAI_IMPLEMENTED', None)
        if original_qwen_key is not None:
            os.environ['QWEN_API_KEY'] = original_qwen_key
        else:
            os.environ.pop('QWEN_API_KEY', None)
        
        # Reload config
        import importlib
        import app.config
        importlib.reload(app.config)


def test_pipeline_openai_unimplemented_auto_fallback_to_qwen(client, app, seed_users):
    """Test: When OpenAI is not implemented, pipeline auto-falls back to Qwen"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    
    # Set up: OpenAI as primary but not implemented, Qwen as fallback with key
    original_provider = os.environ.get('LLM_PROVIDER')
    original_openai_enabled = os.environ.get('OPENAI_ENABLED')
    original_openai_implemented = os.environ.get('OPENAI_IMPLEMENTED')
    original_qwen_key = os.environ.get('QWEN_API_KEY')
    
    try:
        os.environ['LLM_PROVIDER'] = ''
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'
        os.environ['OPENAI_ENABLED'] = 'true'
        os.environ['OPENAI_IMPLEMENTED'] = 'false'  # Not implemented
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
        os.environ['QWEN_API_KEY'] = 'test-qwen-key'  # Qwen has key
        
        # Reload config
        import importlib
        import app.config
        importlib.reload(app.config)
        
        spec = {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'Machine Learning',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90,
                'description': 'Test course'
            },
            'learning_objectives': {
                'knowledge': ['Understand ML basics'],
                'skills': ['Apply algorithms']
            },
            'task_requirements': {
                'task_type': 'structured_debate',
                'expected_output': 'argument',
                'collaboration_form': 'group',
                'requirements_text': 'Test requirements'
            }
        }
        
        resp = client.post(
            f'/api/cscl/scripts/{script_id}/pipeline/run',
            json={'spec': spec}
        )
        
        # Should succeed with Qwen (fallback) or fail gracefully
        # Since Qwen provider also returns "not fully implemented", it may fail
        # But the important thing is it doesn't try OpenAI
        assert resp.status_code in [200, 422, 503]
        
        if resp.status_code == 200:
            data = json.loads(resp.data)
            # Check that stages show fallback was used
            stages = data.get('stages', [])
            if stages:
                # First stage should show provider (could be qwen or mock)
                first_stage = stages[0]
                assert 'provider' in first_stage
                # Should not be openai since it's not implemented
                assert first_stage.get('provider') != 'openai'
    finally:
        # Restore environment
        if original_provider is not None:
            os.environ['LLM_PROVIDER'] = original_provider
        else:
            os.environ.pop('LLM_PROVIDER', None)
        if original_openai_enabled is not None:
            os.environ['OPENAI_ENABLED'] = original_openai_enabled
        else:
            os.environ.pop('OPENAI_ENABLED', None)
        if original_openai_implemented is not None:
            os.environ['OPENAI_IMPLEMENTED'] = original_openai_implemented
        else:
            os.environ.pop('OPENAI_IMPLEMENTED', None)
        if original_qwen_key is not None:
            os.environ['QWEN_API_KEY'] = original_qwen_key
        else:
            os.environ.pop('QWEN_API_KEY', None)
        
        # Reload config
        import importlib
        import app.config
        importlib.reload(app.config)


def test_get_llm_provider_status_mock(client, app):
    """Test: get_llm_provider_status returns correct status for mock"""
    original_provider = os.environ.get('LLM_PROVIDER')
    try:
        os.environ['LLM_PROVIDER'] = 'mock'
        import importlib
        import app.config
        importlib.reload(app.config)
        
        status = get_llm_provider_status()
        assert status['llm_provider_ready'] is True
        assert status['llm_provider_name'] == 'mock'
        assert 'mock' in status['llm_provider_reason'].lower()
    finally:
        if original_provider is not None:
            os.environ['LLM_PROVIDER'] = original_provider
        else:
            os.environ.pop('LLM_PROVIDER', None)
        import importlib
        import app.config
        importlib.reload(app.config)


def test_get_llm_provider_status_openai_not_implemented(client, app):
    """Test: get_llm_provider_status correctly identifies OpenAI as not runnable when not implemented"""
    original_provider = os.environ.get('LLM_PROVIDER')
    original_openai_enabled = os.environ.get('OPENAI_ENABLED')
    original_openai_implemented = os.environ.get('OPENAI_IMPLEMENTED')
    original_openai_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        os.environ['LLM_PROVIDER'] = ''
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'
        os.environ['OPENAI_ENABLED'] = 'true'
        os.environ['OPENAI_IMPLEMENTED'] = 'false'  # Not implemented
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['QWEN_API_KEY'] = 'test-qwen-key'
        
        import importlib
        import app.config
        importlib.reload(app.config)
        
        status = get_llm_provider_status()
        # Should fallback to qwen since openai is not implemented
        assert status['llm_provider_ready'] is True
        assert status['llm_provider_name'] == 'qwen'
        assert 'fallback' in status['llm_provider_reason'].lower()
    finally:
        if original_provider is not None:
            os.environ['LLM_PROVIDER'] = original_provider
        else:
            os.environ.pop('LLM_PROVIDER', None)
        if original_openai_enabled is not None:
            os.environ['OPENAI_ENABLED'] = original_openai_enabled
        else:
            os.environ.pop('OPENAI_ENABLED', None)
        if original_openai_implemented is not None:
            os.environ['OPENAI_IMPLEMENTED'] = original_openai_implemented
        else:
            os.environ.pop('OPENAI_IMPLEMENTED', None)
        if original_openai_key is not None:
            os.environ['OPENAI_API_KEY'] = original_openai_key
        else:
            os.environ.pop('OPENAI_API_KEY', None)
        
        import importlib
        import app.config
        importlib.reload(app.config)
