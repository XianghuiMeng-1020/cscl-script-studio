"""Critic stage - validates and critiques generated script"""
import os
from typing import Dict, Any, List
import time
import logging
from app.services.cscl_llm_provider import BaseLLMProvider, get_cscl_llm_provider
from app.services.pipeline.log_observability import log_stage_stdout

logger = logging.getLogger(__name__)


class CriticStage:
    """Critic stage: validates and critiques generated script"""
    
    def __init__(self, provider: BaseLLMProvider = None):
        self.provider = provider or get_cscl_llm_provider()
    
    def run(self, material_output: Dict[str, Any], spec: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run critic stage
        
        Args:
            material_output: Output from material generator stage
            spec: Normalized pedagogical specification
            options: Generation options
        
        Returns:
            Stage result dict
        """
        start_time = time.time()
        run_id = (options or {}).get('run_id', 'unknown')
        input_snapshot = {
            'material_output': material_output,
            'spec': spec,
            'options': options or {},
            'run_id': run_id
        }
        # Test hook: force critic to fail for reproducible A/B testing (env FORCE_CRITIC_FAIL=1)
        if os.getenv('FORCE_CRITIC_FAIL') == '1':
            latency_ms = int((time.time() - start_time) * 1000)
            log_stage_stdout(run_id, 'critic', 'openai', 'gpt-4o-mini', latency_ms, False, 'forced_fail')
            return {
                'stage_name': 'critic',
                'input_snapshot': input_snapshot,
                'output_snapshot': None,
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': 'failed',
                'error': 'FORCE_CRITIC_FAIL=1 (test hook)'
            }
        try:
            provider_result = self.provider.critique_script({
                "spec": spec,
                "material_output": material_output,
                "options": options or {}
            })
            
            if not provider_result.get('success'):
                latency_ms = int((time.time() - start_time) * 1000)
                run_id = input_snapshot.get('run_id', 'unknown')
                log_stage_stdout(run_id, 'critic', provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, False, 'provider_error')
                return {
                    'stage_name': 'critic',
                    'input_snapshot': input_snapshot,
                    'output_snapshot': None,
                    'provider': provider_result.get('provider', 'unknown'),
                    'model': provider_result.get('model', 'unknown'),
                    'latency_ms': latency_ms,
                    'token_usage': None,
                    'status': 'failed',
                    'error': provider_result.get('error', 'Unknown error')
                }
            
            critique = provider_result.get("critique") or {}
            validation = self._normalize_validation(critique.get("validation", {}))
            quality_indicators = self._normalize_quality_indicators(critique.get("quality_indicators", {}))
            roles = self._normalize_roles(critique.get("roles", []))
            scenes = self._normalize_scenes(critique.get("scenes", []))
            
            # Override: if material has scenes, role-related issues should not fail the whole pipeline
            material_roles = material_output.get("roles") if isinstance(material_output.get("roles"), list) else []
            material_scenes = material_output.get("scenes") if isinstance(material_output.get("scenes"), list) else []
            issues = validation.get("issues") or []
            role_keywords = ["role", "roles defined", "no roles", "insufficient role", "less than"]
            role_issue = any(any(kw in (i or "").lower() for kw in role_keywords) for i in issues)
            if not validation.get("is_valid", True) and role_issue and len(material_scenes) >= 1:
                validation = dict(validation)
                non_role_issues = [i for i in issues if not any(kw in (i or "").lower() for kw in role_keywords)]
                if not non_role_issues:
                    validation["is_valid"] = True
                    validation["issues"] = []
                    validation["warnings"] = (validation.get("warnings") or []) + ["Roles not explicitly defined but script has scenes — treated as valid."]
                else:
                    validation["issues"] = non_role_issues
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            output_snapshot = {
                'scenes': scenes,
                'roles': roles,
                'validation': validation,
                'quality_indicators': quality_indicators
            }
            
            status = 'success' if validation.get('is_valid', True) else 'failed'
            error_msg = '; '.join(validation.get('issues', [])) if validation.get('issues') else None
            
            result = {
                'stage_name': 'critic',
                'input_snapshot': input_snapshot,
                'output_snapshot': output_snapshot,
                'provider': provider_result.get('provider', 'unknown'),
                'model': provider_result.get('model', 'unknown'),
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': status,
                'error': error_msg
            }
            
            logger.info(
                "pipeline_stage run_id=%s stage_name=%s provider=%s model=%s latency_ms=%d success=%s error_type=%s",
                input_snapshot.get('run_id', 'unknown'),
                'critic',
                result['provider'],
                result['model'],
                latency_ms,
                status == 'success',
                'validation_failed' if error_msg else None
            )
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'critic', result['provider'], result['model'], latency_ms, status == 'success', 'validation_failed' if error_msg else None)
            return result
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'critic', 'unknown', 'unknown', latency_ms, False, error_type)
            result = {
                'stage_name': 'critic',
                'input_snapshot': input_snapshot,
                'output_snapshot': None,
                'provider': 'unknown',
                'model': 'unknown',
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': 'failed',
                'error': str(e)
            }
            logger.error(
                "pipeline_stage run_id=%s stage_name=%s provider=%s model=%s latency_ms=%d success=%s error_type=%s",
                input_snapshot.get('run_id', 'unknown'),
                'critic',
                'unknown',
                'unknown',
                latency_ms,
                False,
                error_type
            )
            return result
    
    def _normalize_validation(self, validation: Any) -> Dict[str, Any]:
        """Normalize validation structure"""
        if not isinstance(validation, dict):
            return {'is_valid': True, 'issues': [], 'warnings': []}
        return {
            'is_valid': bool(validation.get('is_valid', True)),
            'issues': validation.get('issues', []) if isinstance(validation.get('issues'), list) else [],
            'warnings': validation.get('warnings', []) if isinstance(validation.get('warnings'), list) else []
        }
    
    def _normalize_quality_indicators(self, indicators: Any) -> Dict[str, Any]:
        """Normalize quality indicators"""
        if not isinstance(indicators, dict):
            return {'scene_count': 0, 'role_count': 0, 'scriptlet_count': 0}
        return {
            'scene_count': int(indicators.get('scene_count', 0)),
            'role_count': int(indicators.get('role_count', 0)),
            'scriptlet_count': int(indicators.get('scriptlet_count', 0))
        }
    
    def _normalize_roles(self, roles: Any) -> List[Dict[str, Any]]:
        """Normalize roles"""
        if not isinstance(roles, list):
            return []
        return [r for r in roles if isinstance(r, dict)]
    
    def _normalize_scenes(self, scenes: Any) -> List[Dict[str, Any]]:
        """Normalize scenes"""
        if not isinstance(scenes, list):
            return []
        return [s for s in scenes if isinstance(s, dict)]
