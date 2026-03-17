"""Refiner stage - refines script based on critic feedback"""
from typing import Dict, Any, List
import time
import logging
from app.services.cscl_llm_provider import BaseLLMProvider, get_cscl_llm_provider
from app.services.pipeline.log_observability import log_stage_stdout

logger = logging.getLogger(__name__)


class RefinerStage:
    """Refiner stage: refines script based on critic feedback"""
    
    def __init__(self, provider: BaseLLMProvider = None):
        self.provider = provider or get_cscl_llm_provider()
    
    def run(self, critic_output: Dict[str, Any], spec: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run refiner stage
        
        Args:
            critic_output: Output from critic stage
            spec: Normalized pedagogical specification
            options: Generation options
        
        Returns:
            Stage result dict
        """
        start_time = time.time()
        input_snapshot = {
            'critic_output': critic_output,
            'spec': spec,
            'options': options or {},
            'run_id': (options or {}).get('run_id', 'unknown')
        }
        
        try:
            provider_result = self.provider.refine_script({
                "spec": spec,
                "critic_output": critic_output,
                "options": options or {}
            })
            
            if not provider_result.get('success'):
                latency_ms = int((time.time() - start_time) * 1000)
                run_id = input_snapshot.get('run_id', 'unknown')
                log_stage_stdout(run_id, 'refiner', provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, False, 'provider_error')
                return {
                    'stage_name': 'refiner',
                    'input_snapshot': input_snapshot,
                    'output_snapshot': None,
                    'provider': provider_result.get('provider', 'unknown'),
                    'model': provider_result.get('model', 'unknown'),
                    'latency_ms': latency_ms,
                    'token_usage': None,
                    'status': 'failed',
                    'error': provider_result.get('error', 'Unknown error')
                }
            
            refined = provider_result.get("refined") or {}
            roles = self._normalize_roles(refined.get("roles", []))
            scenes = self._normalize_scenes(refined.get("scenes", []))
            refinements_applied = self._normalize_refinements(refined.get("refinements_applied", {}))
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            output_snapshot = {
                'scenes': scenes,
                'roles': roles,
                'refinements_applied': refinements_applied
            }
            # Pass through classroom-ready artefacts (from refined output or critic input)
            for key in ('student_worksheet', 'student_slides', 'teacher_guide', 'role_cards'):
                if refined.get(key):
                    output_snapshot[key] = refined[key]
                elif critic_output.get(key):
                    output_snapshot[key] = critic_output[key]
            
            result = {
                'stage_name': 'refiner',
                'input_snapshot': input_snapshot,
                'output_snapshot': output_snapshot,
                'provider': provider_result.get('provider', 'unknown'),
                'model': provider_result.get('model', 'unknown'),
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': 'success',
                'error': None
            }
            
            logger.info(
                "pipeline_stage run_id=%s stage_name=%s provider=%s model=%s latency_ms=%d success=%s error_type=%s",
                input_snapshot.get('run_id', 'unknown'),
                'refiner',
                result['provider'],
                result['model'],
                latency_ms,
                True,
                None
            )
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'refiner', result['provider'], result['model'], latency_ms, True, None)
            return result
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'refiner', 'unknown', 'unknown', latency_ms, False, error_type)
            result = {
                'stage_name': 'refiner',
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
                'refiner',
                'unknown',
                'unknown',
                latency_ms,
                False,
                error_type
            )
            return result
    
    def _normalize_roles(self, roles: Any) -> List[Dict[str, Any]]:
        """Normalize roles"""
        if not isinstance(roles, list):
            return []
        normalized = []
        for r in roles:
            if not isinstance(r, dict):
                continue
            normalized.append({
                'role_name': str(r.get('role_name', 'unknown')),
                'responsibilities': r.get('responsibilities', []) if isinstance(r.get('responsibilities'), list) else []
            })
        return normalized
    
    def _normalize_scenes(self, scenes: Any) -> List[Dict[str, Any]]:
        """Normalize scenes"""
        if not isinstance(scenes, list):
            return []
        normalized = []
        for s in scenes:
            if not isinstance(s, dict):
                continue
            scriptlets = s.get('scriptlets', [])
            if not isinstance(scriptlets, list):
                scriptlets = []
            normalized_scriptlets = []
            for sl in scriptlets:
                if not isinstance(sl, dict):
                    continue
                normalized_scriptlets.append({
                    'prompt_text': str(sl.get('prompt_text', '')),
                    'prompt_type': str(sl.get('prompt_type', 'claim')),
                    'role_id': sl.get('role_id')
                })
            normalized.append({
                'order_index': int(s.get('order_index', len(normalized) + 1)),
                'scene_type': str(s.get('scene_type', 'unknown')),
                'purpose': str(s.get('purpose', '')),
                'transition_rule': str(s.get('transition_rule', '')),
                'scriptlets': normalized_scriptlets
            })
        return normalized
    
    def _normalize_refinements(self, refinements: Any) -> Dict[str, Any]:
        """Normalize refinements_applied"""
        if not isinstance(refinements, dict):
            return {}
        return {
            'scenes_added': int(refinements.get('scenes_added', 0)),
            'roles_added': int(refinements.get('roles_added', 0)),
            'scriptlets_fixed': int(refinements.get('scriptlets_fixed', 0))
        }
