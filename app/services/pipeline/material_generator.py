"""Material Generator stage - generates scriptlets and materials"""
from typing import Dict, Any, List
import time
import logging
from app.services.cscl_llm_provider import get_cscl_llm_provider, BaseLLMProvider
from app.services.pipeline.log_observability import log_stage_stdout

logger = logging.getLogger(__name__)


class MaterialGeneratorStage:
    """Material Generator stage: generates scriptlets and materials"""
    
    def __init__(self, provider: BaseLLMProvider = None):
        self.provider = provider or get_cscl_llm_provider()
    
    def run(self, planner_output: Dict[str, Any], spec: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run material generator stage
        
        Args:
            planner_output: Output from planner stage
            spec: Normalized pedagogical specification
            options: Generation options
        
        Returns:
            Stage result dict
        """
        start_time = time.time()
        input_snapshot = {
            'planner_output': planner_output,
            'spec': spec,
            'options': options or {},
            'run_id': (options or {}).get('run_id', 'unknown')
        }
        
        try:
            provider_result = self.provider.generate_materials({
                "spec": spec,
                "planner_output": planner_output,
                "options": options or {}
            })
            
            if not provider_result.get('success'):
                latency_ms = int((time.time() - start_time) * 1000)
                run_id = input_snapshot.get('run_id', 'unknown')
                log_stage_stdout(run_id, 'material_generator', provider_result.get('provider', 'unknown'), provider_result.get('model', 'unknown'), latency_ms, False, 'provider_error')
                return {
                    'stage_name': 'material_generator',
                    'input_snapshot': input_snapshot,
                    'output_snapshot': None,
                    'provider': provider_result.get('provider', 'unknown'),
                    'model': provider_result.get('model', 'unknown'),
                    'latency_ms': latency_ms,
                    'token_usage': None,
                    'status': 'failed',
                    'error': provider_result.get('error', 'Unknown error')
                }
            
            materials = provider_result.get("materials") or {}
            roles = self._normalize_roles(materials.get("roles", []))
            scenes = self._normalize_scenes(materials.get("scenes", []))
            student_worksheet = materials.get("student_worksheet")
            teacher_guide = materials.get("teacher_guide")
            role_cards = materials.get("role_cards", [])
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            output_snapshot = {
                'scenes': scenes,
                'roles': roles,
                'materials_generated': len(scenes),
                'student_worksheet': student_worksheet,
                'teacher_guide': teacher_guide,
                'role_cards': role_cards
            }
            
            result = {
                'stage_name': 'material_generator',
                'input_snapshot': input_snapshot,
                'output_snapshot': output_snapshot,
                'provider': provider_result.get('provider', 'unknown'),
                'model': provider_result.get('model', 'unknown'),
                'latency_ms': latency_ms,
                'token_usage': None,
                'status': 'success',
                'error': None
            }
            
            # Structured logging
            logger.info(
                "pipeline_stage run_id=%s stage_name=%s provider=%s model=%s latency_ms=%d success=%s error_type=%s",
                input_snapshot.get('run_id', 'unknown'),
                'material_generator',
                result['provider'],
                result['model'],
                latency_ms,
                True,
                None
            )
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'material_generator', result['provider'], result['model'], latency_ms, True, None)
            return result
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_type = type(e).__name__
            log_stage_stdout(input_snapshot.get('run_id', 'unknown'), 'material_generator', 'unknown', 'unknown', latency_ms, False, error_type)
            result = {
                'stage_name': 'material_generator',
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
                'material_generator',
                'unknown',
                'unknown',
                latency_ms,
                False,
                error_type
            )
            return result
    
    def _normalize_roles(self, roles: Any) -> List[Dict[str, Any]]:
        """Normalize roles to safe structure"""
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
        """Normalize scenes to safe structure"""
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
    
    def _generate_detailed_prompt(self, scriptlet: Dict[str, Any], spec: Dict[str, Any], roles: list) -> str:
        """Generate detailed prompt text for scriptlet"""
        prompt_type = scriptlet.get('prompt_type', 'claim')
        topic = spec['course_context']['topic']
        
        prompt_templates = {
            'claim': f'State your position on {topic}. Provide a clear claim supported by reasoning.',
            'evidence': f'Present evidence that supports your position on {topic}. Cite specific examples or data.',
            'counterargument': f'Present a counterargument to the position on {topic}. Challenge assumptions and provide alternative perspectives.',
            'synthesis': f'Synthesize the key points discussed about {topic}. Identify areas of agreement and disagreement.'
        }
        
        return prompt_templates.get(prompt_type, scriptlet.get('prompt_text', f'Engage with {topic}'))
