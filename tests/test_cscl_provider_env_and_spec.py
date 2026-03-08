"""Tests: provider env alias (CSCL_* / LLM_*), get_cscl_llm_provider, _get_single_provider, spec task_type validation."""
import os
import pytest
import importlib


def test_resolve_provider_env_only_llm_vars():
    """Only LLM_* set -> selection uses them."""
    mod = __import__('app.services.cscl_llm_provider', fromlist=['_resolve_provider_env'])
    try:
        os.environ.pop('CSCL_LLM_PROVIDER', None)
        os.environ.pop('CSCL_LLM_PRIMARY', None)
        os.environ.pop('CSCL_LLM_FALLBACK', None)
        os.environ.pop('CSCL_LLM_STRATEGY', None)
        os.environ['LLM_PROVIDER'] = 'qwen'
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        os.environ['LLM_PROVIDER_FALLBACK'] = 'qwen'
        os.environ['LLM_STRATEGY'] = 'single'
        importlib.reload(mod)
        r = mod._resolve_provider_env()
        assert r['provider'] == 'qwen'
        assert r['primary'] == 'openai'
        assert r['fallback'] == 'qwen'
        assert r['strategy'] == 'single'
    finally:
        for k in ['LLM_PROVIDER', 'LLM_PROVIDER_PRIMARY', 'LLM_PROVIDER_FALLBACK', 'LLM_STRATEGY']:
            os.environ.pop(k, None)


def test_resolve_provider_env_only_cscl_vars():
    """Only CSCL_* set -> selection uses them."""
    mod = __import__('app.services.cscl_llm_provider', fromlist=['_resolve_provider_env'])
    try:
        os.environ.pop('LLM_PROVIDER', None)
        os.environ.pop('LLM_PROVIDER_PRIMARY', None)
        os.environ.pop('LLM_PROVIDER_FALLBACK', None)
        os.environ.pop('LLM_STRATEGY', None)
        os.environ['CSCL_LLM_PROVIDER'] = 'openai'
        os.environ['CSCL_LLM_PRIMARY'] = 'qwen'
        os.environ['CSCL_LLM_FALLBACK'] = 'openai'
        os.environ['CSCL_LLM_STRATEGY'] = 'primary_with_fallback'
        importlib.reload(mod)
        r = mod._resolve_provider_env()
        assert r['provider'] == 'openai'
        assert r['primary'] == 'qwen'
        assert r['fallback'] == 'openai'
        assert r['strategy'] == 'primary_with_fallback'
    finally:
        for k in ['CSCL_LLM_PROVIDER', 'CSCL_LLM_PRIMARY', 'CSCL_LLM_FALLBACK', 'CSCL_LLM_STRATEGY']:
            os.environ.pop(k, None)


def test_resolve_provider_env_cscl_wins_over_llm():
    """Both set -> CSCL_* wins."""
    mod = __import__('app.services.cscl_llm_provider', fromlist=['_resolve_provider_env'])
    try:
        os.environ['CSCL_LLM_PRIMARY'] = 'qwen'
        os.environ['LLM_PROVIDER_PRIMARY'] = 'openai'
        importlib.reload(mod)
        r = mod._resolve_provider_env()
        assert r['primary'] == 'qwen'
    finally:
        os.environ.pop('CSCL_LLM_PRIMARY', None)
        os.environ.pop('LLM_PROVIDER_PRIMARY', None)


def test_get_cscl_llm_provider_force_qwen_returns_instance():
    """get_cscl_llm_provider(force_provider='qwen') returns concrete provider instance."""
    from app.services.cscl_llm_provider import get_cscl_llm_provider, QwenProvider
    p = get_cscl_llm_provider(force_provider='qwen')
    assert p is not None
    assert isinstance(p, QwenProvider)


def test_get_cscl_llm_provider_force_openai_returns_instance():
    """get_cscl_llm_provider(force_provider='openai') returns concrete provider instance."""
    from app.services.cscl_llm_provider import get_cscl_llm_provider, OpenAIProvider
    p = get_cscl_llm_provider(force_provider='openai')
    assert p is not None
    assert isinstance(p, OpenAIProvider)


def test_get_single_provider_unknown_raises_value_error():
    """_get_single_provider(unknown) raises ValueError."""
    from app.services.cscl_llm_provider import _get_single_provider
    with pytest.raises(ValueError) as exc_info:
        _get_single_provider('unknown_provider')
    assert 'Unsupported provider' in str(exc_info.value) or 'unknown_provider' in str(exc_info.value)


def test_spec_validator_accepts_structured_debate():
    """Spec validation accepts task_type from config taxonomy (e.g. structured_debate)."""
    from app.services.spec_validator import SpecValidator
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Topic',
            'class_size': 20,
            'mode': 'sync',
            'duration': 60,
            'description': 'Desc'
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'out',
            'collaboration_form': 'group',
            'requirements_text': 'req'
        }
    }
    result = SpecValidator.validate(spec_data)
    assert result['valid'] is True, result.get('issues')


def test_spec_validator_rejects_unknown_task_type_with_valid_ids_message():
    """Spec validator rejects unknown task_type and message lists valid IDs from get_valid_task_type_ids()."""
    from app.services.spec_validator import SpecValidator
    from app.services.task_type_config import get_valid_task_type_ids
    valid_ids = get_valid_task_type_ids()
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Topic',
            'class_size': 20,
            'mode': 'sync',
            'duration': 60,
            'description': 'Desc'
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'invalid_task_type_xyz',
            'expected_output': 'out',
            'collaboration_form': 'group',
            'requirements_text': 'req'
        }
    }
    result = SpecValidator.validate(spec_data)
    assert result['valid'] is False
    assert 'task_requirements.task_type' in (result.get('field_paths') or [])
    issues_text = ' '.join(result.get('issues', []))
    for vid in valid_ids:
        assert vid in issues_text, f"Valid ID {vid} should appear in error message: {issues_text}"
