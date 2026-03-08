"""S2.18 Tests: Provider selection single point and fail-fast"""
import pytest
import json
import os
from app.db import db
from app.models import User, UserRole, CSCLScript
from app.services.cscl_llm_provider import select_runnable_provider, get_llm_provider_status, is_provider_runnable


def test_select_runnable_provider_never_picks_unimplemented_openai(client, app):
    """Test: select_runnable_provider never picks unimplemented OpenAI when LLM_ALLOW_UNIMPLEMENTED_PRIMARY=false"""
    original_openai_enabled = os.environ.get('OPENAI_ENABLED')
    original_openai_implemented = os.environ.get('OPENAI_IMPLEMENTED')
    original_openai_key = os.environ.get('OPENAI_API_KEY')
    original_allow = os.environ.get('LLM_ALLOW_UNIMPLEMENTED_PRIMARY')
    original_primary = os.environ.get('LLM_PROVIDER_PRIMARY')
    original_qwen_key = os.environ.get('QWEN_API_KEY')
    original_qwen_enabled = os.environ.get('QWEN_ENABLED')
    original_qwen_implemented = os.environ.get('QWEN_IMPLEMENTED')
    
    try:
        # Set OpenAI as primary but not implemented
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'
        os.environ['OPENAI_ENABLED'] = 'true'
        os.environ['OPENAI_IMPLEMENTED'] = 'false'  # Not implemented
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['LLM_ALLOW_UNIMPLEMENTED_PRIMARY'] = 'false'  # Must not allow
        os.environ['QWEN_API_KEY'] = 'test-qwen-key'
        os.environ['QWEN_ENABLED'] = 'true'
        os.environ['QWEN_IMPLEMENTED'] = 'true'
        
        # Reload config
        import importlib
        import app.config
        importlib.reload(app.config)
        importlib.reload(app.services.cscl_llm_provider)
        
        status = select_runnable_provider()
        
        # Should select qwen (fallback), not openai
        assert status['provider'] == 'qwen', f"Expected qwen, got {status['provider']}"
        assert status['provider'] != 'openai'
        assert 'fallback' in status['reason'].lower() or 'not runnable' in status['reason'].lower()
    finally:
        # Restore
        for key, value in [
            ('OPENAI_ENABLED', original_openai_enabled),
            ('OPENAI_IMPLEMENTED', original_openai_implemented),
            ('OPENAI_API_KEY', original_openai_key),
            ('LLM_ALLOW_UNIMPLEMENTED_PRIMARY', original_allow),
            ('LLM_PROVIDER_PRIMARY', original_primary),
            ('QWEN_API_KEY', original_qwen_key),
            ('QWEN_ENABLED', original_qwen_enabled),
            ('QWEN_IMPLEMENTED', original_qwen_implemented),
        ]:
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
        
        import importlib
        import app.config
        importlib.reload(app.config)


def test_pipeline_returns_503_when_no_runnable_provider(client, app, seed_users):
    """Test: pipeline/run returns 503 LLM_PROVIDER_NOT_READY when no provider is runnable, stages=[]"""
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
    
    # Set up: No runnable provider
    original_provider = os.environ.get('LLM_PROVIDER')
    original_openai_enabled = os.environ.get('OPENAI_ENABLED')
    original_openai_implemented = os.environ.get('OPENAI_IMPLEMENTED')
    original_qwen_key = os.environ.get('QWEN_API_KEY')
    original_qwen_enabled = os.environ.get('QWEN_ENABLED')
    original_qwen_implemented = os.environ.get('QWEN_IMPLEMENTED')
    original_allow = os.environ.get('LLM_ALLOW_UNIMPLEMENTED_PRIMARY')
    original_primary = os.environ.get('LLM_PROVIDER_PRIMARY')
    
    try:
        os.environ['LLM_PROVIDER'] = ''
        os.environ['LLM_PROVIDER_PRIMARY'] = 'qwen'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'openai'
        os.environ['QWEN_API_KEY'] = ''  # No Qwen key
        os.environ['QWEN_ENABLED'] = 'true'
        os.environ['QWEN_IMPLEMENTED'] = 'true'
        os.environ['OPENAI_ENABLED'] = 'false'
        os.environ['OPENAI_IMPLEMENTED'] = 'false'
        os.environ['LLM_ALLOW_UNIMPLEMENTED_PRIMARY'] = 'false'
        
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
        
        # Should return 503 with LLM_PROVIDER_NOT_READY, stages=[]
        assert resp.status_code == 503, f"Expected 503, got {resp.status_code}"
        data = json.loads(resp.data)
        assert data.get('code') == 'LLM_PROVIDER_NOT_READY', f"Expected LLM_PROVIDER_NOT_READY, got {data.get('code')}"
        assert 'error' in data
        assert 'details' in data
        assert 'primary' in data['details']
        assert 'fallback' in data['details']
        assert 'stages' in data
        assert data['stages'] == [], f"Expected empty stages, got {data['stages']}"
    finally:
        # Restore
        for key, value in [
            ('LLM_PROVIDER', original_provider),
            ('OPENAI_ENABLED', original_openai_enabled),
            ('OPENAI_IMPLEMENTED', original_openai_implemented),
            ('QWEN_API_KEY', original_qwen_key),
            ('QWEN_ENABLED', original_qwen_enabled),
            ('QWEN_IMPLEMENTED', original_qwen_implemented),
            ('LLM_ALLOW_UNIMPLEMENTED_PRIMARY', original_allow),
            ('LLM_PROVIDER_PRIMARY', original_primary),
        ]:
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
        
        import importlib
        import app.config
        importlib.reload(app.config)


def test_pipeline_no_duplicate_retry_when_primary_equals_fallback(client, app, seed_users):
    """Test: Pipeline does not retry when primary equals fallback (no qwen->qwen retry)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
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
    
    # Set up: primary=qwen, fallback=qwen (same)
    original_provider = os.environ.get('LLM_PROVIDER')
    original_primary = os.environ.get('LLM_PROVIDER_PRIMARY')
    original_fallback = os.environ.get('LLM_PROVIDER_FALLBACK')
    original_qwen_key = os.environ.get('QWEN_API_KEY')
    original_qwen_enabled = os.environ.get('QWEN_ENABLED')
    original_qwen_implemented = os.environ.get('QWEN_IMPLEMENTED')
    
    try:
        os.environ['LLM_PROVIDER'] = ''
        os.environ['LLM_PROVIDER_PRIMARY'] = 'qwen'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'  # Same as primary
        os.environ['QWEN_API_KEY'] = ''  # No key, so not runnable
        os.environ['QWEN_ENABLED'] = 'true'
        os.environ['QWEN_IMPLEMENTED'] = 'true'
        
        import importlib
        import app.config
        importlib.reload(app.config)
        
        spec = {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'ML',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90,
                'description': 'Test'
            },
            'learning_objectives': {
                'knowledge': ['Test'],
                'skills': ['Test']
            },
            'task_requirements': {
                'task_type': 'structured_debate',
                'expected_output': 'argument',
                'collaboration_form': 'group',
                'requirements_text': 'Test'
            }
        }
        
        resp = client.post(
            f'/api/cscl/scripts/{script_id}/pipeline/run',
            json={'spec': spec}
        )
        
        # Should return 503 immediately, no duplicate retry
        assert resp.status_code == 503
        data = json.loads(resp.data)
        assert data.get('code') == 'LLM_PROVIDER_NOT_READY'
        assert len(data.get('stages', [])) == 0  # No stages created
    finally:
        for key, value in [
            ('LLM_PROVIDER', original_provider),
            ('LLM_PROVIDER_PRIMARY', original_primary),
            ('LLM_PROVIDER_FALLBACK', original_fallback),
            ('QWEN_API_KEY', original_qwen_key),
            ('QWEN_ENABLED', original_qwen_enabled),
            ('QWEN_IMPLEMENTED', original_qwen_implemented),
        ]:
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
        
        import importlib
        import app.config
        importlib.reload(app.config)


def test_health_exposes_provider_readiness_fields(client, app):
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
