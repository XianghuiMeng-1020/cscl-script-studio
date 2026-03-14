"""Planner stage - generates initial script structure"""
from typing import Dict, Any
import time
import logging
from app.services.cscl_llm_provider import get_cscl_llm_provider, BaseLLMProvider
from app.services.pipeline.log_observability import log_stage_stdout

logger = logging.getLogger(__name__)


class PlannerStage:
    """Planner stage: generates initial script structure"""
    
    def __init__(self, provider: BaseLLMProvider = None):
        self.provider = provider or get_cscl_llm_provider()
    
    def run(self, spec: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run planner stage
        
        Args:
            spec: Normalized pedagogical specification
            options: Generation options (temperature, max_tokens, etc.)
        
        Returns:
            {
                'stage_name': 'planner',
                'input_snapshot': {...},
                'output_snapshot': {...},
                'provider': str,
                'model': str,
                'latency_ms': int,
                'token_usage': dict or None,
                'status': 'success' | 'failed' | 'skipped',
                'error': str or None
            }
        """
        start_time = time.time()
        run_id = (options or {}).get('run_id', 'unknown')
        input_snapshot = {
            'spec': spec,
            'options': options or {},
            'run_id': run_id
        }
        
        try:
            # Prepare input for provider (activity-centred: one specific collaborative activity)
            cc = spec.get('course_context') or {}
            tr = spec.get('task_requirements') or {}
            input_payload = {
                'topic': cc.get('topic'),
                'learning_objectives': spec.get('learning_objectives'),
                'task_type': tr.get('task_type'),
                'duration_minutes': cc.get('duration', 60),
                'retrieved_chunks': spec.get('retrieved_chunks', []),
                'teaching_stage': spec.get('teaching_stage', 'concept_exploration'),
                'collaboration_purpose': spec.get('collaboration_purpose', 'compare_ideas'),
                'group_size': spec.get('group_size', 4),
                'grouping_strategy': spec.get('grouping_strategy', 'random'),
                'role_structure': spec.get('role_structure', 'no_roles'),
                'whole_class_reporting': spec.get('whole_class_reporting', True),
                'expected_output': tr.get('expected_output'),
                'requirements_text': tr.get('requirements_text'),
                'scaffolding_options': spec.get('scaffolding_options', []),
                'student_difficulties': spec.get('student_difficulties', ''),
                'class_size': cc.get('class_size'),
                'mode': cc.get('mode', 'sync'),
                'initial_idea': (spec.get('initial_idea') or '').strip() or None
            }
            
            # Call provider
            result = self.provider.generate_script_plan(input_payload)
            
            latency_ms = int((time.time() - start_time) * 1000)
            provider_name = result.get('provider', 'unknown')
            model_name = result.get('model', 'unknown')
            success = result.get('success', False)
            error_type = None if success else 'provider_error'
            
            # 结构化日志
            if success:
                logger.info(
                    "pipeline_stage run_id=%s stage_name=planner provider=%s model=%s latency_ms=%d success=true error_type=None",
                    run_id, provider_name, model_name, latency_ms
                )
            else:
                logger.error(
                    "pipeline_stage run_id=%s stage_name=planner provider=%s model=%s latency_ms=%d success=false error_type=%s",
                    run_id, provider_name, model_name, latency_ms, error_type
                )
            log_stage_stdout(run_id, 'planner', provider_name, model_name, latency_ms, success, error_type)
            
            if not success:
                return {
                    'stage_name': 'planner',
                    'input_snapshot': input_snapshot,
                    'output_snapshot': None,
                    'provider': provider_name,
                    'model': model_name,
                    'latency_ms': latency_ms,
                    'token_usage': None,
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }
            
            plan_raw = result.get('plan') or {}
            activity = plan_raw.get('activity') or plan_raw
            # Backward compatibility: build scenes/roles from activity if present
            scenes = plan_raw.get('scenes') or []
            roles = plan_raw.get('roles') or []
            if activity and not scenes and activity.get('steps'):
                for s in activity.get('steps', []):
                    scenes.append({
                        'order_index': s.get('step_order', len(scenes) + 1),
                        'scene_type': 'task_step',
                        'purpose': s.get('description') or s.get('title', ''),
                        'transition_rule': '',
                        'scriptlets': [{'prompt_text': p, 'prompt_type': 'discussion', 'role_id': None} for p in (s.get('prompts') or [])]
                    })
            if activity and not roles and activity.get('roles'):
                for r in activity.get('roles', []):
                    roles.append({
                        'role_id': r.get('role_name', ''),
                        'role_name': r.get('role_name', ''),
                        'description': r.get('description', ''),
                        'responsibilities': r.get('responsibilities', [])
                    })
            output_snapshot = {
                'plan': {**plan_raw, 'scenes': scenes, 'roles': roles},
                'activity': activity if isinstance(activity, dict) and activity.get('title') else None,
                'scenes': scenes,
                'roles': roles
            }
            
            return {
                'stage_name': 'planner',
                'input_snapshot': input_snapshot,
                'output_snapshot': output_snapshot,
                'provider': provider_name,
                'model': model_name,
                'latency_ms': latency_ms,
                'token_usage': result.get('token_usage'),
                'status': 'success',
                'error': None
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__
            logger.error(
                "pipeline_stage run_id=%s stage_name=planner provider=unknown model=unknown latency_ms=%d success=false error_type=%s",
                run_id, latency_ms, error_type
            )
            log_stage_stdout(run_id, 'planner', 'unknown', 'unknown', latency_ms, False, error_type)
            return {
                'stage_name': 'planner',
                'input_snapshot': input_snapshot,
                'output_snapshot': None,
                'provider': 'unknown',
                'model': 'unknown',
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': 'failed',
                'error': str(e)
            }
