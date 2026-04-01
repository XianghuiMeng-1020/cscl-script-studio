"""CriticRefiner stage - evaluates AND refines in a single LLM call (merged from separate Critic + Refiner)"""
import os
from typing import Dict, Any, List
import time
import logging
from app.services.cscl_llm_provider import BaseLLMProvider, get_cscl_llm_provider
from app.services.pipeline.log_observability import log_stage_stdout

logger = logging.getLogger(__name__)


class CriticRefinerStage:
    """Combined critic + refiner: evaluates quality then fixes issues in one pass"""

    def __init__(self, provider: BaseLLMProvider = None):
        self.provider = provider or get_cscl_llm_provider()

    def run(self, material_output: Dict[str, Any], spec: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        start_time = time.time()
        run_id = (options or {}).get('run_id', 'unknown')
        input_snapshot = {
            'material_output': material_output,
            'spec': spec,
            'options': options or {},
            'run_id': run_id
        }

        if os.getenv('FORCE_CRITIC_FAIL') == '1':
            latency_ms = int((time.time() - start_time) * 1000)
            log_stage_stdout(run_id, 'critic_refiner', 'test', 'test', latency_ms, False, 'forced_fail')
            return {
                'stage_name': 'critic_refiner',
                'input_snapshot': input_snapshot,
                'output_snapshot': None,
                'provider': 'test', 'model': 'test',
                'latency_ms': latency_ms, 'token_usage': None,
                'status': 'failed',
                'error': 'FORCE_CRITIC_FAIL=1 (test hook)'
            }

        try:
            provider_result = self.provider.critique_and_refine({
                "spec": spec,
                "material_output": material_output,
                "options": options or {}
            })

            if not provider_result.get('success'):
                latency_ms = int((time.time() - start_time) * 1000)
                log_stage_stdout(run_id, 'critic_refiner', provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, False, 'provider_error')
                return {
                    'stage_name': 'critic_refiner',
                    'input_snapshot': input_snapshot,
                    'output_snapshot': None,
                    'provider': provider_result.get('provider', 'unknown'),
                    'model': provider_result.get('model', 'unknown'),
                    'latency_ms': latency_ms, 'token_usage': None,
                    'status': 'failed',
                    'error': provider_result.get('error', 'Unknown error')
                }

            result_data = provider_result.get('result') or {}
            validation = self._normalize_validation(result_data.get('validation', {}))
            quality_indicators = self._normalize_quality_indicators(result_data.get('quality_indicators', {}))
            roles = self._normalize_roles(result_data.get('roles', []))
            scenes = self._normalize_scenes(result_data.get('scenes', []))
            refinements = result_data.get('refinements_applied', {})

            # Relaxation: role-only issues should not block if we have scenes
            material_scenes = material_output.get('scenes') if isinstance(material_output.get('scenes'), list) else []
            issues = validation.get('issues') or []
            role_kw = ["role", "roles defined", "no roles", "insufficient role", "less than"]
            role_issue = any(any(kw in (i or "").lower() for kw in role_kw) for i in issues)
            if not validation.get('is_valid', True) and role_issue and len(material_scenes) >= 1:
                validation = dict(validation)
                non_role = [i for i in issues if not any(kw in (i or "").lower() for kw in role_kw)]
                if not non_role:
                    validation["is_valid"] = True
                    validation["issues"] = []
                    validation["warnings"] = (validation.get("warnings") or []) + ["Roles not explicitly defined but script has scenes — treated as valid."]
                else:
                    validation["issues"] = non_role

            latency_ms = int((time.time() - start_time) * 1000)

            output_snapshot = {
                'scenes': scenes,
                'roles': roles,
                'validation': validation,
                'quality_indicators': quality_indicators,
                'refinements_applied': refinements
            }
            for key in ('student_worksheet', 'student_slides', 'teacher_guide', 'role_cards'):
                if result_data.get(key):
                    output_snapshot[key] = result_data[key]
                elif material_output.get(key):
                    output_snapshot[key] = material_output[key]

            status = 'success' if validation.get('is_valid', True) else 'failed'
            error_msg = '; '.join(validation.get('issues', [])) if validation.get('issues') else None

            logger.info(
                "pipeline_stage run_id=%s stage_name=critic_refiner provider=%s model=%s latency_ms=%d success=%s",
                run_id, provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, status == 'success'
            )
            log_stage_stdout(run_id, 'critic_refiner', provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, status == 'success', 'validation_failed' if error_msg else None)

            return {
                'stage_name': 'critic_refiner',
                'input_snapshot': input_snapshot,
                'output_snapshot': output_snapshot,
                'provider': provider_result.get('provider', 'unknown'),
                'model': provider_result.get('model', 'unknown'),
                'latency_ms': latency_ms, 'token_usage': None,
                'status': status,
                'error': error_msg
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            log_stage_stdout(run_id, 'critic_refiner', 'unknown', 'unknown', latency_ms, False, type(e).__name__)
            logger.error("pipeline_stage run_id=%s stage_name=critic_refiner error=%s", run_id, str(e))
            return {
                'stage_name': 'critic_refiner',
                'input_snapshot': input_snapshot,
                'output_snapshot': None,
                'provider': 'unknown', 'model': 'unknown',
                'latency_ms': latency_ms, 'token_usage': None,
                'status': 'failed',
                'error': str(e)
            }

    def _normalize_validation(self, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            return {'is_valid': True, 'issues': [], 'warnings': []}
        return {
            'is_valid': bool(v.get('is_valid', True)),
            'issues': v.get('issues', []) if isinstance(v.get('issues'), list) else [],
            'warnings': v.get('warnings', []) if isinstance(v.get('warnings'), list) else []
        }

    def _normalize_quality_indicators(self, ind: Any) -> Dict[str, Any]:
        if not isinstance(ind, dict):
            return {'scene_count': 0, 'role_count': 0, 'scriptlet_count': 0}
        return {
            'scene_count': int(ind.get('scene_count', 0)),
            'role_count': int(ind.get('role_count', 0)),
            'scriptlet_count': int(ind.get('scriptlet_count', 0))
        }

    def _normalize_roles(self, roles: Any) -> List[Dict[str, Any]]:
        if not isinstance(roles, list):
            return []
        out = []
        for r in roles:
            if not isinstance(r, dict):
                continue
            out.append({
                'role_name': str(r.get('role_name', 'unknown')),
                'responsibilities': r.get('responsibilities', []) if isinstance(r.get('responsibilities'), list) else []
            })
        return out

    def _normalize_scenes(self, scenes: Any) -> List[Dict[str, Any]]:
        if not isinstance(scenes, list):
            return []
        out = []
        for s in scenes:
            if not isinstance(s, dict):
                continue
            scriptlets = s.get('scriptlets', [])
            if not isinstance(scriptlets, list):
                scriptlets = []
            norm_sl = []
            for sl in scriptlets:
                if not isinstance(sl, dict):
                    continue
                norm_sl.append({
                    'prompt_text': str(sl.get('prompt_text', '')),
                    'prompt_type': str(sl.get('prompt_type', 'claim')),
                    'role_id': sl.get('role_id')
                })
            out.append({
                'order_index': int(s.get('order_index', len(out) + 1)),
                'scene_type': str(s.get('scene_type', 'unknown')),
                'purpose': str(s.get('purpose', '')),
                'transition_rule': str(s.get('transition_rule', '')),
                'scriptlets': norm_sl
            })
        return out
