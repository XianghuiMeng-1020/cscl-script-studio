"""CSCL Script LLM Provider abstraction layer.
S2.10: Primary+fallback (GPT primary, Qwen fallback); fallback only on timeout/429/5xx/connection.
Structured log: request_id, primary_provider, final_provider, fallback_triggered, error_type, latency_ms.
S2.18: Unified provider selection and readiness checking.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import requests
import json
import time
import uuid
import logging
from flask import current_app, has_app_context
from app.config import Config

logger = logging.getLogger(__name__)


def _as_int(value: Any, default: int) -> int:
    """Parse value as int; return default if invalid."""
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


# Retryable error patterns: trigger fallback. 401/403/parameter errors must NOT fallback.
# S2.18: Add "not fully implemented" as retryable to trigger fallback
_RETRYABLE_ERROR_PATTERNS = (
    'timeout', 'timed out', '429', '503', '502', '500', '504',
    'connection', 'connect', 'network', 'unavailable',
    'not fully implemented', 'not implemented'
)
_NON_RETRYABLE_PATTERNS = ('401', '403', 'unauthorized', 'forbidden', 'invalid', 'parameter', 'validation')


def _is_retryable_error(err_msg: str) -> bool:
    """True if error message matches retryable patterns (trigger fallback)."""
    if not err_msg:
        return False
    msg = err_msg.lower()
    for p in _NON_RETRYABLE_PATTERNS:
        if p in msg:
            return False
    for p in _RETRYABLE_ERROR_PATTERNS:
        if p in msg:
            return True
    return False


def _error_type(err_msg: str) -> str:
    """Classify error for logging."""
    if not err_msg:
        return 'unknown'
    msg = err_msg.lower()
    for p in _NON_RETRYABLE_PATTERNS:
        if p in msg:
            return p
    for p in _RETRYABLE_ERROR_PATTERNS:
        if p in msg:
            return p
    return 'unknown'


def _get_config_value(key: str, default: Any = None) -> Any:
    """
    S2.18: Get config value with priority: current_app.config > os.environ > Config default.
    """
    if has_app_context():
        try:
            value = current_app.config.get(key)
            if value is not None:
                return value
        except Exception:
            pass
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    return getattr(Config, key, default)


def _resolve_provider_env() -> Dict[str, str]:
    """
    Resolve provider env vars with backward compatibility.
    CSCL_* takes precedence over LLM_*.
    Returns: provider, primary, fallback, strategy (all lowercased).
    """
    provider = (
        _get_config_value('CSCL_LLM_PROVIDER') or
        _get_config_value('LLM_PROVIDER') or
        'qwen'
    )
    primary = (
        _get_config_value('CSCL_LLM_PRIMARY') or
        _get_config_value('LLM_PROVIDER_PRIMARY') or
        provider
    )
    fallback = (
        _get_config_value('CSCL_LLM_FALLBACK') or
        _get_config_value('LLM_PROVIDER_FALLBACK') or
        'openai'
    )
    strategy = (
        _get_config_value('CSCL_LLM_STRATEGY') or
        _get_config_value('LLM_STRATEGY') or
        'single'
    )
    return {
        'provider': str(provider).lower().strip() if provider else 'qwen',
        'primary': str(primary).lower().strip() if primary else 'qwen',
        'fallback': str(fallback).lower().strip() if fallback else 'openai',
        'strategy': str(strategy).lower().strip() if strategy else 'single',
    }


def is_provider_runnable(provider_name: str) -> Dict[str, Any]:
    """
    S2.18: Unified provider runnability check. Returns {provider, runnable, reason}.
    """
    provider_name = (provider_name or '').lower()
    if provider_name == 'mock':
        return {'provider': 'mock', 'runnable': True, 'reason': 'Mock provider is always runnable'}
    if provider_name == 'openai':
        enabled = _get_config_value('OPENAI_ENABLED', 'false')
        enabled = str(enabled).lower() == 'true' if enabled is not None else False
        implemented = _get_config_value('OPENAI_IMPLEMENTED', 'false')
        implemented = str(implemented).lower() == 'true' if implemented is not None else False
        allow_unimplemented = _get_config_value('LLM_ALLOW_UNIMPLEMENTED_PRIMARY', 'false')
        allow_unimplemented = str(allow_unimplemented).lower() == 'true' if allow_unimplemented is not None else False
        api_key = _get_config_value('OPENAI_API_KEY', '') or ''
        if not enabled:
            return {'provider': 'openai', 'runnable': False, 'reason': 'OPENAI_ENABLED is false'}
        if not implemented and not allow_unimplemented:
            return {'provider': 'openai', 'runnable': False, 'reason': 'OPENAI_IMPLEMENTED is false and LLM_ALLOW_UNIMPLEMENTED_PRIMARY is false'}
        if not api_key:
            return {'provider': 'openai', 'runnable': False, 'reason': 'OPENAI_API_KEY is not configured'}
        return {'provider': 'openai', 'runnable': True, 'reason': 'OpenAI is enabled and has API key'}
    if provider_name == 'qwen':
        enabled = _get_config_value('QWEN_ENABLED', 'true')
        enabled = str(enabled).lower() == 'true' if enabled is not None else True
        implemented = _get_config_value('QWEN_IMPLEMENTED', 'true')
        implemented = str(implemented).lower() == 'true' if implemented is not None else True
        api_key = (_get_config_value('QWEN_API_KEY', '') or '') or (_get_config_value('DASHSCOPE_API_KEY', '') or '')
        if not enabled:
            return {'provider': 'qwen', 'runnable': False, 'reason': 'QWEN_ENABLED is false'}
        if not implemented:
            return {'provider': 'qwen', 'runnable': False, 'reason': 'QWEN_IMPLEMENTED is false'}
        if not api_key:
            return {'provider': 'qwen', 'runnable': False, 'reason': 'QWEN_API_KEY/DASHSCOPE_API_KEY is not configured'}
        return {'provider': 'qwen', 'runnable': True, 'reason': 'Qwen is enabled, implemented, and has API key'}
    return {'provider': provider_name, 'runnable': False, 'reason': f'Unknown provider: {provider_name}'}


class BaseLLMProvider(ABC):
    """Base interface for LLM providers for CSCL script generation"""
    
    @property
    def name(self) -> str:
        return "base"

    def is_ready(self) -> bool:
        return True
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if provider is ready to use"""
        pass
    
    @abstractmethod
    def generate_script_plan(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate script plan based on input
        
        Args:
            input_payload: {
                'topic': str,
                'learning_objectives': list,
                'task_type': str,
                'duration_minutes': int,
                'retrieved_chunks': list (optional)
            }
        
        Returns:
            {
                'success': bool,
                'plan': dict (scenes/roles/scriptlets structure),
                'error': Optional[str],
                'provider': str,
                'model': str
            }
        """
        pass
    
    @abstractmethod
    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate materials (roles, scenes)"""
        pass
    
    @abstractmethod
    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Critique script and return validation/quality indicators"""
        pass
    
    @abstractmethod
    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Refine script based on critique"""
        pass


class MockProvider(BaseLLMProvider):
    """Mock provider for testing and fallback"""
    
    @property
    def name(self) -> str:
        return "mock"
    
    def generate_script_plan(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deterministic mock script plan"""
        topic = input_payload.get('topic', 'Unknown Topic')
        objectives = input_payload.get('learning_objectives', [])
        task_type = input_payload.get('task_type', 'structured_debate')
        retrieved_chunks = input_payload.get('retrieved_chunks', [])
        
        # Generate mock plan based on template structure
        plan = {
            'scenes': [
                {
                    'order_index': 1,
                    'scene_type': 'opening',
                    'purpose': f'Introduce {topic} and establish initial positions',
                    'transition_rule': 'Move to confrontation when all participants have stated initial positions',
                    'scriptlets': [
                        {
                            'prompt_text': f'Introduce yourself and state your initial position on: {topic}',
                            'prompt_type': 'claim',
                            'role_id': None
                        }
                    ]
                },
                {
                    'order_index': 2,
                    'scene_type': 'confrontation',
                    'purpose': f'Present conflicting viewpoints about {topic}',
                    'transition_rule': 'Proceed to argumentation when key conflicts are identified',
                    'scriptlets': [
                        {
                            'prompt_text': f'Present evidence that supports your position on {topic}',
                            'prompt_type': 'evidence',
                            'role_id': None,
                            'resource_ref': retrieved_chunks[0]['ref'] if retrieved_chunks else None
                        }
                    ]
                },
                {
                    'order_index': 3,
                    'scene_type': 'argumentation',
                    'purpose': f'Develop arguments about {topic}',
                    'transition_rule': 'Advance to conclusion when arguments are sufficiently developed',
                    'scriptlets': [
                        {
                            'prompt_text': f'Develop your argument further with additional evidence',
                            'prompt_type': 'evidence',
                            'role_id': None
                        }
                    ]
                },
                {
                    'order_index': 4,
                    'scene_type': 'conclusion',
                    'purpose': f'Synthesize findings about {topic}',
                    'transition_rule': 'End script when synthesis is complete',
                    'scriptlets': [
                        {
                            'prompt_text': f'Synthesize the key points discussed about {topic}',
                            'prompt_type': 'synthesis',
                            'role_id': None
                        }
                    ]
                }
            ],
            'roles': [
                {
                    'role_name': 'advocate',
                    'responsibilities': [f'Present position on {topic}', 'Defend arguments']
                },
                {
                    'role_name': 'challenger',
                    'responsibilities': [f'Question assumptions about {topic}', 'Present counterarguments']
                }
            ]
        }
        
        return {
            'success': True,
            'plan': plan,
            'error': None,
            'provider': 'mock',
            'model': Config.MOCK_MODEL
        }
    
    def is_ready(self) -> bool:
        return True
    
    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        plan = self.generate_script_plan(input_payload)
        if not plan.get('success'):
            return {'success': False, 'error': plan.get('error'), 'provider': 'mock', 'model': Config.MOCK_MODEL, 'materials': None}
        materials = plan.get('plan', {})
        return {'success': True, 'error': None, 'provider': 'mock', 'model': Config.MOCK_MODEL, 'materials': materials}
    
    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        material_output = input_payload.get('material_output', {})
        scenes = material_output.get('scenes', [])
        roles = material_output.get('roles', [])
        total_scriptlets = sum(len(s.get('scriptlets', [])) for s in scenes)
        critique = {
            'validation': {'is_valid': True, 'issues': [], 'warnings': []},
            'quality_indicators': {
                'scene_count': len(scenes),
                'role_count': len(roles),
                'scriptlet_count': total_scriptlets
            },
            'roles': roles,
            'scenes': scenes
        }
        return {'success': True, 'error': None, 'provider': 'mock', 'model': Config.MOCK_MODEL, 'critique': critique}
    
    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        critic_output = input_payload.get('critic_output', {})
        scenes = critic_output.get('scenes', [])
        roles = critic_output.get('roles', [])
        refined = {
            'roles': roles,
            'scenes': scenes,
            'refinements_applied': {}
        }
        return {'success': True, 'error': None, 'provider': 'mock', 'model': Config.MOCK_MODEL, 'refined': refined}
    
    def is_ready(self) -> bool:
        return True
    
    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        plan = input_payload.get('planner_output', {}).get('plan', {})
        return {
            'success': True,
            'error': None,
            'provider': 'mock',
            'model': Config.MOCK_MODEL,
            'materials': {
                'roles': plan.get('roles', []),
                'scenes': plan.get('scenes', [])
            }
        }
    
    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        scenes = input_payload.get('material_output', {}).get('scenes', [])
        roles = input_payload.get('material_output', {}).get('roles', [])
        scriptlet_count = sum(len(s.get('scriptlets', [])) for s in scenes)
        return {
            'success': True,
            'error': None,
            'provider': 'mock',
            'model': Config.MOCK_MODEL,
            'critique': {
                'validation': {'is_valid': True, 'issues': [], 'warnings': []},
                'quality_indicators': {
                    'scene_count': len(scenes),
                    'role_count': len(roles),
                    'scriptlet_count': scriptlet_count
                },
                'roles': roles,
                'scenes': scenes
            }
        }
    
    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        scenes = input_payload.get('critic_output', {}).get('scenes', [])
        roles = input_payload.get('critic_output', {}).get('roles', [])
        return {
            'success': True,
            'error': None,
            'provider': 'mock',
            'model': Config.MOCK_MODEL,
            'refined': {
                'roles': roles,
                'scenes': scenes,
                'refinements_applied': {}
            }
        }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider (implemented)"""

    @property
    def name(self) -> str:
        return "openai"

    def is_ready(self) -> bool:
        api_key = (
            os.getenv('OPENAI_API_KEY', '') or str(_get_config_value('OPENAI_API_KEY', ''))
        )
        return bool(api_key and api_key.strip())

    def generate_script_plan(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        model = str(_get_config_value('OPENAI_MODEL', 'gpt-4o-mini'))
        base_url = str(_get_config_value('OPENAI_BASE_URL', 'https://api.openai.com/v1')).rstrip('/')
        timeout_s = int(_as_int(_get_config_value('OPENAI_TIMEOUT_SECONDS', 120), 120))

        if not self.is_ready():
            return {
                'success': False,
                'plan': None,
                'error': 'OPENAI_API_KEY not configured',
                'provider': 'openai',
                'model': model
            }

        api_key = (
            os.getenv('OPENAI_API_KEY', '') or str(_get_config_value('OPENAI_API_KEY', ''))
        ).strip()

        try:
            user_text = json.dumps(input_payload, ensure_ascii=False)
            messages = [
                {"role": "system", "content": "You are a CSCL script planner. Return ONLY valid JSON."},
                {"role": "user", "content": f"Generate a script plan JSON from this payload: {user_text}"}
            ]

            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3
                },
                timeout=timeout_s
            )

            if resp.status_code >= 400:
                return {
                    'success': False,
                    'plan': None,
                    'error': f"OpenAI API HTTP {resp.status_code}: {resp.text[:400]}",
                    'provider': 'openai',
                    'model': model
                }

            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )

            if not content:
                return {
                    'success': False,
                    'plan': None,
                    'error': 'OpenAI API returned empty content',
                    'provider': 'openai',
                    'model': model
                }

            # 尝试解析 JSON；若不是 JSON 则原样回传给上层处理
            plan_obj = None
            try:
                plan_obj = json.loads(content)
            except Exception:
                plan_obj = {"raw_text": content}

            return {
                'success': True,
                'plan': plan_obj,
                'error': None,
                'provider': 'openai',
                'model': model
            }

        except Exception as e:
            return {
                'success': False,
                'plan': None,
                'error': f"OpenAI request failed: {type(e).__name__}: {e}",
                'provider': 'openai',
                'model': model
            }
    
    def _chat_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic chat JSON method for OpenAI API calls"""
        api_key = (
            os.getenv('OPENAI_API_KEY', '') or str(_get_config_value('OPENAI_API_KEY', ''))
        )
        model = str(_get_config_value('OPENAI_MODEL', 'gpt-4o-mini'))
        base_url = str(_get_config_value('OPENAI_BASE_URL', 'https://api.openai.com/v1')).rstrip('/')
        timeout_s = int(_as_int(_get_config_value('OPENAI_TIMEOUT_SECONDS', 120), 120))

        if not api_key:
            return {
                'success': False, 'error': 'OPENAI_API_KEY not configured',
                'provider': 'openai', 'model': model, 'output': None
            }

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
            ]

            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0},
                timeout=timeout_s
            )

            if resp.status_code >= 400:
                return {
                    'success': False,
                    'error': f"OpenAI API HTTP {resp.status_code}: {resp.text[:500]}",
                    'provider': 'openai',
                    'model': model,
                    'output': None
                }

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not content:
                return {
                    'success': False,
                    'error': 'OpenAI API returned empty content',
                    'provider': 'openai',
                    'model': model,
                    'output': None
                }

            try:
                parsed = json.loads(content)
            except Exception:
                # 容错：提取 markdown code fence 内 JSON
                txt = content.strip()
                if "```" in txt:
                    parts = txt.split("```")
                    if len(parts) >= 3:
                        txt = parts[-2]
                    txt = txt.replace("json", "", 1).strip()
                try:
                    parsed = json.loads(txt)
                except Exception:
                    parsed = {"raw_text": content}

            return {
                'success': True,
                'error': None,
                'provider': 'openai',
                'model': model,
                'output': parsed
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"OpenAI request failed: {type(e).__name__}: {e}",
                'provider': 'openai',
                'model': model,
                'output': None
            }
    
    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "You generate CSCL materials. Return ONLY JSON with keys: "
            "roles (list), scenes (list). "
            "Each scene must include: order_index, scene_type, purpose, transition_rule, scriptlets. "
            "Each scriptlet must include: prompt_text, prompt_type, role_id (nullable)."
        )
        r = self._chat_json(system_prompt, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'materials': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'materials': out}
    
    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        material_output = input_payload.get('material_output') or {}
        roles = material_output.get('roles') if isinstance(material_output.get('roles'), list) else []
        scenes = material_output.get('scenes') if isinstance(material_output.get('scenes'), list) else []
        role_count = len(roles)
        scene_count = len(scenes)
        role_names = [r.get('role_name', '') for r in roles if isinstance(r, dict)][:20]
        scriptlet_count = sum(len(s.get('scriptlets') or []) for s in scenes if isinstance(s, dict))
        # Build a compact payload to avoid timeout on large specs
        compact_payload = {
            'role_count': role_count,
            'scene_count': scene_count,
            'scriptlet_count': scriptlet_count,
            'role_names': role_names,
            'roles': roles[:10],  # limit
            'scenes': [
                {
                    'order_index': s.get('order_index'),
                    'scene_type': s.get('scene_type'),
                    'purpose': s.get('purpose', '')[:200],
                    'scriptlet_count': len(s.get('scriptlets') or []),
                    'scriptlets': (s.get('scriptlets') or [])[:3]  # first 3 scriptlets per scene
                }
                for s in scenes[:10] if isinstance(s, dict)
            ],
            'spec_topic': (input_payload.get('spec') or {}).get('topic', ''),
            'spec_task_type': (input_payload.get('spec') or {}).get('task_type', ''),
        }
        system_prompt = (
            "You are a CSCL script critic. Return ONLY JSON with keys: "
            "validation {is_valid:boolean, issues:list[str], warnings:list[str]}, "
            "quality_indicators {scene_count:int, role_count:int, scriptlet_count:int}, "
            "roles (list), scenes (list). "
            "Rule: If the script has at least 2 roles and 2 scenes, set is_valid to true "
            "unless there are real quality issues (e.g. empty scriptlets, missing scene types). "
            "Do NOT report 'No roles defined' or 'No scenes' when roles and scenes are non-empty."
        )
        r = self._chat_json(system_prompt, compact_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'critique': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'critique': out}
    
    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "You are a CSCL script refiner. Fix issues and return ONLY JSON with keys: "
            "roles (list), scenes (list), refinements_applied (object). "
            "Ensure at least 2 roles, 2 scenes, and non-empty scriptlets."
        )
        r = self._chat_json(system_prompt, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'refined': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'refined': out}


class QwenProvider(BaseLLMProvider):
    """Qwen provider (implemented)"""

    @property
    def name(self) -> str:
        return "qwen"

    def is_ready(self) -> bool:
        api_key = (
            os.getenv('QWEN_API_KEY', '') or str(_get_config_value('QWEN_API_KEY', '')) or
            os.getenv('DASHSCOPE_API_KEY', '') or str(_get_config_value('DASHSCOPE_API_KEY', ''))
        )
        return bool(api_key and str(api_key).strip())

    def generate_script_plan(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        model = str(_get_config_value('QWEN_MODEL', 'qwen-plus'))
        base_url = str(_get_config_value('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')).rstrip('/')
        timeout_s = int(_as_int(_get_config_value('QWEN_TIMEOUT_SECONDS', 120), 120))

        if not self.is_ready():
            return {
                'success': False,
                'plan': None,
                'error': 'QWEN_API_KEY not configured',
                'provider': 'qwen',
                'model': model
            }

        api_key = (
            os.getenv('QWEN_API_KEY', '') or str(_get_config_value('QWEN_API_KEY', '')) or
            os.getenv('DASHSCOPE_API_KEY', '') or str(_get_config_value('DASHSCOPE_API_KEY', ''))
        )

        try:
            user_text = json.dumps(input_payload, ensure_ascii=False)
            messages = [
                {"role": "system", "content": "You are a CSCL script planner. Return ONLY valid JSON."},
                {"role": "user", "content": f"Generate a script plan JSON from this payload: {user_text}"}
            ]

            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3
                },
                timeout=timeout_s
            )

            if resp.status_code >= 400:
                err_text = (resp.text or '')[:400]
                # 401 invalid_api_key: 返回可操作的提示，便于用户在 .env 中修正密钥
                if resp.status_code == 401 and ('invalid_api_key' in err_text or 'Incorrect API key' in err_text or 'incorrect api key' in err_text.lower()):
                    error_msg = (
                        'Qwen API 密钥无效。请在 .env 中设置正确的 QWEN_API_KEY（或 DASHSCOPE_API_KEY），'
                        '或在阿里云控制台获取/更新密钥：https://help.aliyun.com/zh/model-studio/error-code#apikey-error'
                    )
                else:
                    error_msg = f"Qwen API HTTP {resp.status_code}: {err_text}"
                return {
                    'success': False,
                    'plan': None,
                    'error': error_msg,
                    'provider': 'qwen',
                    'model': model
                }

            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )

            if not content:
                return {
                    'success': False,
                    'plan': None,
                    'error': 'Qwen API returned empty content',
                    'provider': 'qwen',
                    'model': model
                }

            # 尝试解析 JSON；若不是 JSON 则原样回传给上层处理
            plan_obj = None
            try:
                plan_obj = json.loads(content)
            except Exception:
                plan_obj = {"raw_text": content}

            return {
                'success': True,
                'plan': plan_obj,
                'error': None,
                'provider': 'qwen',
                'model': model
            }

        except Exception as e:
            return {
                'success': False,
                'plan': None,
                'error': f"Qwen request failed: {type(e).__name__}: {e}",
                'provider': 'qwen',
                'model': model
            }
    
    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Qwen generate_materials - forward to generate_script_plan for now"""
        plan_result = self.generate_script_plan(input_payload)
        if not plan_result.get('success'):
            return {'success': False, 'error': plan_result.get('error'), 'provider': 'qwen', 'model': plan_result.get('model', 'qwen-plus'), 'materials': None}
        materials = plan_result.get('plan', {})
        return {'success': True, 'error': None, 'provider': 'qwen', 'model': plan_result.get('model', 'qwen-plus'), 'materials': materials}
    
    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Qwen critique_script - return structured failure for now"""
        return {'success': False, 'error': 'Qwen critique_script not implemented', 'provider': 'qwen', 'model': str(_get_config_value('QWEN_MODEL', 'qwen-plus')), 'critique': None}
    
    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Qwen refine_script - return structured failure for now"""
        return {'success': False, 'error': 'Qwen refine_script not implemented', 'provider': 'qwen', 'model': str(_get_config_value('QWEN_MODEL', 'qwen-plus')), 'refined': None}

class FallbackLLMProvider(BaseLLMProvider):
    """S2.10: Primary then fallback; fallback only on timeout/429/5xx/connection. Structured logging.
    S2.18: Records stage_attempts for pipeline logging."""

    def __init__(self, primary: BaseLLMProvider, fallback: BaseLLMProvider,
                 primary_name: str = 'openai', fallback_name: str = 'qwen'):
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name

    @property
    def name(self) -> str:
        return f"{self.primary_name}+{self.fallback_name}"

    def is_ready(self) -> bool:
        """Ready if at least one sub-provider is ready."""
        return self.primary.is_ready() or self.fallback.is_ready()

    # ---- internal helper: run method with primary-then-fallback ----

    def _call_with_fallback(self, method_name: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic primary → fallback dispatcher for any provider method."""
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        primary_provider = self.primary_name
        final_provider = primary_provider
        fallback_triggered = False
        error_type = None
        stage_attempts = []

        # Attempt primary
        primary_fn = getattr(self.primary, method_name)
        primary_start = time.perf_counter()
        try:
            result = primary_fn(input_payload)
        except Exception as exc:
            result = {'success': False, 'error': str(exc)}
        primary_latency_ms = int((time.perf_counter() - primary_start) * 1000)
        stage_attempts.append({
            'provider': primary_provider,
            'status': 'success' if result.get('success') else 'failed',
            'error': result.get('error'),
            'latency_ms': primary_latency_ms
        })

        if result.get('success'):
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_payload = {
                "request_id": request_id,
                "method": method_name,
                "primary_provider": primary_provider,
                "final_provider": final_provider,
                "fallback_triggered": fallback_triggered,
                "error_type": error_type,
                "latency_ms": latency_ms,
            }
            logger.info("cscl_llm_request %s", json.dumps(log_payload))
            result['stage_attempts'] = stage_attempts
            return result

        err_msg = result.get('error') or ''
        if _is_retryable_error(err_msg):
            error_type = _error_type(err_msg)
            fallback_triggered = True
            fallback_fn = getattr(self.fallback, method_name)
            fallback_start = time.perf_counter()
            try:
                result_fb = fallback_fn(input_payload)
            except Exception as exc:
                result_fb = {'success': False, 'error': str(exc)}
            fallback_latency_ms = int((time.perf_counter() - fallback_start) * 1000)
            stage_attempts.append({
                'provider': self.fallback_name,
                'status': 'success' if result_fb.get('success') else 'failed',
                'error': result_fb.get('error'),
                'latency_ms': fallback_latency_ms
            })
            latency_ms = int((time.perf_counter() - start) * 1000)
            final_provider = self.fallback_name
            if result_fb.get('success'):
                result = result_fb
            log_payload = {
                "request_id": request_id,
                "method": method_name,
                "primary_provider": primary_provider,
                "final_provider": final_provider,
                "fallback_triggered": fallback_triggered,
                "error_type": error_type,
                "latency_ms": latency_ms,
            }
            logger.info("cscl_llm_request %s", json.dumps(log_payload))
            result['stage_attempts'] = stage_attempts
            return result

        latency_ms = int((time.perf_counter() - start) * 1000)
        log_payload = {
            "request_id": request_id,
            "method": method_name,
            "primary_provider": primary_provider,
            "final_provider": final_provider,
            "fallback_triggered": False,
            "error_type": _error_type(err_msg),
            "latency_ms": latency_ms,
        }
        logger.info("cscl_llm_request %s", json.dumps(log_payload))
        result['stage_attempts'] = stage_attempts
        return result

    # ---- abstract method implementations ----

    def generate_script_plan(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback('generate_script_plan', input_payload)

    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback('generate_materials', input_payload)

    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback('critique_script', input_payload)

    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback('refine_script', input_payload)


def _get_single_provider(provider_name: str) -> BaseLLMProvider:
    """Construct one concrete provider instance by name. Supports openai and qwen; ValueError for unsupported."""
    name = (provider_name or "").lower().strip()
    if name == "openai":
        return OpenAIProvider()
    if name == "qwen":
        return QwenProvider()
    if name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")


def select_runnable_provider() -> Dict[str, Any]:
    """
    S2.18: Single point of provider selection. Returns detailed status.
    Uses _resolve_provider_env() for CSCL_* / LLM_* backward compatibility.
    
    Returns:
        {
            ready: bool,
            provider: str,
            reason: str,
            primary: str,
            fallback: str,
            strategy: str,
            checks: Dict[str, Dict[str, Any]]  # {primary: {...}, fallback: {...}}
        }
    """
    resolved = _resolve_provider_env()
    forced_provider = resolved['provider']
    if forced_provider == 'mock':
        return {
            'ready': True,
            'provider': 'mock',
            'reason': 'Mock provider forced via CSCL_LLM_PROVIDER/LLM_PROVIDER=mock',
            'primary': 'mock',
            'fallback': 'mock',
            'strategy': 'single',
            'checks': {
                'primary': {'provider': 'mock', 'runnable': True, 'reason': 'Mock forced'}
            }
        }
    
    primary_name = resolved['primary']
    fallback_name = resolved['fallback']
    strategy = resolved['strategy']
    # Normalize strategy: primary_with_fallback/fallback_only => same branch; single => single branch
    if strategy not in ('primary_with_fallback', 'fallback_only'):
        strategy = 'single'
    
    # Check runnability
    primary_check = is_provider_runnable(primary_name)
    fallback_check = is_provider_runnable(fallback_name)
    
    checks = {
        'primary': primary_check,
        'fallback': fallback_check
    }
    
    # Strategy-based selection
    if strategy in ('primary_with_fallback', 'fallback_only'):
        # Try primary first
        if primary_check['runnable']:
            return {
                'ready': True,
                'provider': primary_name,
                'reason': f'Primary provider {primary_name} is runnable',
                'primary': primary_name,
                'fallback': fallback_name,
                'strategy': strategy,
                'checks': checks
            }
        
        # Try fallback only if different from primary and runnable
        if fallback_name != primary_name and fallback_check['runnable']:
            return {
                'ready': True,
                'provider': fallback_name,
                'reason': f'Primary {primary_name} not runnable ({primary_check["reason"]}), using fallback {fallback_name}',
                'primary': primary_name,
                'fallback': fallback_name,
                'strategy': strategy,
                'checks': checks
            }
        
        # Neither runnable
        return {
            'ready': False,
            'provider': primary_name,  # Return primary for error reporting
            'reason': f'Neither primary {primary_name} ({primary_check["reason"]}) nor fallback {fallback_name} ({fallback_check["reason"]}) is runnable',
            'primary': primary_name,
            'fallback': fallback_name,
            'strategy': strategy,
            'checks': checks
        }
    else:
        # Single provider mode
        if primary_check['runnable']:
            return {
                'ready': True,
                'provider': primary_name,
                'reason': f'Provider {primary_name} is runnable',
                'primary': primary_name,
                'fallback': fallback_name,
                'strategy': strategy,
                'checks': checks
            }
        else:
            return {
                'ready': False,
                'provider': primary_name,
                'reason': f'Provider {primary_name} is not runnable: {primary_check["reason"]}',
                'primary': primary_name,
                'fallback': fallback_name,
                'strategy': strategy,
                'checks': checks
            }


def get_llm_provider_status() -> Dict[str, Any]:
    """
    S2.18: Get LLM provider readiness status for health endpoint.
    Uses select_runnable_provider() as single point of selection.
    Returns: {
        'llm_provider_ready': bool,
        'llm_provider_name': str,
        'llm_provider_reason': str,
        'llm_primary': str,
        'llm_fallback': str,
        'llm_strategy': str
    }
    """
    status = select_runnable_provider()
    
    return {
        'llm_provider_ready': status['ready'],
        'llm_provider_name': status['provider'],
        'llm_provider_reason': status['reason'],
        'llm_primary': status['primary'],
        'llm_fallback': status['fallback'],
        'llm_strategy': status['strategy']
    }


def get_cscl_llm_provider(force_provider: Optional[str] = None) -> BaseLLMProvider:
    """
    Get CSCL LLM provider.
    S2.18: Uses select_runnable_provider() as single point of selection.
    
    Args:
        force_provider: Optional provider name to force (e.g., 'qwen' for retry)
    
    Returns:
        BaseLLMProvider instance
    """
    # Force provider (for retry scenarios)
    if force_provider:
        return _get_single_provider(force_provider.lower())
    
    # S2.18: Use single point of selection
    status = select_runnable_provider()
    provider_name = status['provider']
    primary_name = status['primary']
    fallback_name = status['fallback']
    strategy = status['strategy']
    
    # If strategy allows fallback and both are runnable and different, wrap in FallbackLLMProvider
    if strategy == 'primary_with_fallback' and primary_name != fallback_name:
        primary_check = status['checks']['primary']
        fallback_check = status['checks']['fallback']
        
        if primary_check['runnable'] and fallback_check['runnable']:
            return FallbackLLMProvider(
                _get_single_provider(primary_name),
                _get_single_provider(fallback_name),
                primary_name=primary_name,
                fallback_name=fallback_name,
            )
    
    # Single provider mode or fallback not available
    if not provider_name:
        raise RuntimeError("No runnable LLM provider resolved (provider_name is empty). Check env/provider config.")
    return _get_single_provider(provider_name)
