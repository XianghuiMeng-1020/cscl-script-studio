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
            # Prepare input for provider
            input_payload = {
                'topic': spec['course_context']['topic'],
                'learning_objectives': spec['learning_objectives'],
                'task_type': spec['task_requirements']['task_type'],
                'duration_minutes': spec['course_context']['duration'],
                'retrieved_chunks': spec.get('retrieved_chunks', [])
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
            
            output_snapshot = {
                'plan': result.get('plan', {}),
                'scenes': result.get('plan', {}).get('scenes', []),
                'roles': result.get('plan', {}).get('roles', [])
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
