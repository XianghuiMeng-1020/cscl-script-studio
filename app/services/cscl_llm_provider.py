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


def _should_retry_status(status_code: int) -> bool:
    return status_code in (408, 429, 500, 502, 503, 504)


def _post_json_with_retry(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout_s: int,
    max_retries: int = 1
):
    """
    HTTP POST with bounded retry for transient failures.
    max_retries means additional attempts after the first call.
    """
    retries = max(0, int(max_retries))
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=max(10, int(timeout_s)),
            )
            if resp.status_code < 400:
                return resp, None
            if _should_retry_status(resp.status_code) and attempt < retries:
                time.sleep(min(1.5 * (attempt + 1), 4))
                continue
            return resp, None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(min(1.5 * (attempt + 1), 4))
                continue
            return None, last_error
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            return None, last_error
    return None, last_error or "unknown request error"


def _resolve_provider_env() -> Dict[str, str]:
    """
    Resolve provider env vars with backward compatibility.
    CSCL_* takes precedence over LLM_*.
    Returns: provider, primary, fallback, strategy (all lowercased).
    """
    provider = (
        _get_config_value('CSCL_LLM_PROVIDER') or
        _get_config_value('LLM_PROVIDER') or
        'openai'
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
        'provider': str(provider).lower().strip() if provider else 'openai',
        'primary': str(primary).lower().strip() if primary else 'openai',
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

    def critique_and_refine(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Combined critique + refine in one call. Default: delegates to critique_script."""
        return self.critique_script(input_payload)


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
        import copy
        critic_output = input_payload.get('critic_output', {})
        scenes = copy.deepcopy(critic_output.get('scenes', []))
        roles = copy.deepcopy(critic_output.get('roles', []))
        
        # Apply realistic refinements
        refinements_applied = {
            'scenes_added': 0,
            'roles_added': 0,
            'scriptlets_fixed': 0
        }
        
        # Refinement 1: Ensure at least one opening scene exists
        has_opening = any(s.get('scene_type') == 'opening' for s in scenes)
        if not has_opening and scenes:
            scenes.insert(0, {
                'order_index': 1,
                'scene_type': 'opening',
                'purpose': 'Introduce the activity and clarify expectations',
                'transition_rule': 'Teacher announces group assignments and distributes materials',
                'scriptlets': [
                    {'prompt_text': 'Review the activity goals and expected output with your group', 'prompt_type': 'instruction', 'role_id': None}
                ]
            })
            # Reorder indices
            for i, s in enumerate(scenes):
                s['order_index'] = i + 1
            refinements_applied['scenes_added'] += 1
        
        # Refinement 2: Ensure at least one conclusion scene exists
        has_conclusion = any(s.get('scene_type') == 'conclusion' for s in scenes)
        if not has_conclusion and len(scenes) > 1:
            scenes.append({
                'order_index': len(scenes) + 1,
                'scene_type': 'conclusion',
                'purpose': 'Synthesize findings and prepare for whole-class sharing',
                'transition_rule': 'Groups finalize their outputs and prepare to report',
                'scriptlets': [
                    {'prompt_text': 'Prepare a 2-minute summary of your group\'s key findings to share with the class', 'prompt_type': 'synthesis', 'role_id': None}
                ]
            })
            refinements_applied['scenes_added'] += 1
        
        # Refinement 3: Add role-specific scriptlets where missing
        for scene in scenes:
            scriptlets = scene.get('scriptlets', [])
            if len(scriptlets) < 2 and roles:
                # Add a role-specific prompt
                for role in roles[:1]:
                    scriptlets.append({
                        'prompt_text': f"As {role.get('role_name', 'your role')}, identify one key evidence point that supports or challenges the main claim",
                        'prompt_type': 'evidence',
                        'role_id': role.get('role_name')
                    })
                    refinements_applied['scriptlets_fixed'] += 1
            scene['scriptlets'] = scriptlets
        
        # Refinement 4: Ensure at least 2 roles exist for group work
        if len(roles) < 2:
            default_roles = [
                {'role_name': 'facilitator', 'responsibilities': ['Keep discussion on track', 'Ensure all voices are heard']},
                {'role_name': 'recorder', 'responsibilities': ['Document key points and decisions', 'Prepare summary for sharing']},
                {'role_name': 'evidence_checker', 'responsibilities': ['Verify claims against sources', 'Request citations when needed']}
            ]
            for role in default_roles:
                if len(roles) < 3:
                    roles.append(role)
                    refinements_applied['roles_added'] += 1
        
        refined = {
            'roles': roles,
            'scenes': scenes,
            'refinements_applied': refinements_applied
        }
        return {'success': True, 'error': None, 'provider': 'mock', 'model': Config.MOCK_MODEL, 'refined': refined}

    def critique_and_refine(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        material_output = input_payload.get('material_output', {})
        scenes = material_output.get('scenes', [])
        roles = material_output.get('roles', [])
        result = {
            'validation': {'is_valid': True, 'issues': [], 'warnings': []},
            'quality_indicators': {'scene_count': len(scenes), 'role_count': len(roles), 'scriptlet_count': sum(len(s.get('scriptlets', [])) for s in scenes)},
            'roles': roles,
            'scenes': scenes,
            'refinements_applied': {'scenes_added': 0, 'roles_added': 0, 'scriptlets_fixed': 0, 'prompts_made_specific': 0, 'grounding_added': 0},
        }
        for key in ('student_worksheet', 'student_slides', 'teacher_guide', 'role_cards'):
            if material_output.get(key):
                result[key] = material_output[key]
        return {'success': True, 'error': None, 'provider': 'mock', 'model': Config.MOCK_MODEL, 'result': result}

    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        planner_output = input_payload.get('planner_output', {})
        plan = planner_output.get('plan', {})
        activity = planner_output.get('activity') or plan.get('activity', {})
        spec = input_payload.get('spec', {})
        cc = spec.get('course_context', {})
        topic = cc.get('topic', 'Unknown Topic')

        roles = plan.get('roles', [])
        scenes = plan.get('scenes', [])

        steps = activity.get('steps', []) if isinstance(activity, dict) else []
        roles_summary = ', '.join(
            r.get('role_name', '') for r in (activity.get('roles') or roles) if isinstance(r, dict)
        ) or 'No specific roles assigned'

        worksheet_steps = []
        for i, s in enumerate(steps):
            worksheet_steps.append({
                'step_order': s.get('step_order', i + 1),
                'title': s.get('title', f'Step {i + 1}'),
                'description': s.get('description', ''),
                'duration_minutes': s.get('duration_minutes', 5),
                'prompts': s.get('prompts', [])
            })
        if not worksheet_steps:
            for i, sc in enumerate(scenes):
                worksheet_steps.append({
                    'step_order': i + 1,
                    'title': sc.get('purpose', f'Step {i + 1}')[:80],
                    'description': sc.get('purpose', ''),
                    'duration_minutes': 5,
                    'prompts': [sl.get('prompt_text', '') for sl in (sc.get('scriptlets') or [])]
                })

        student_worksheet = {
            'title': activity.get('title', f'{topic} – Collaborative Activity') if isinstance(activity, dict) else f'{topic} – Collaborative Activity',
            'goal': activity.get('objective', f'Collaboratively explore {topic}') if isinstance(activity, dict) else f'Collaboratively explore {topic}',
            'roles_summary': roles_summary,
            'steps': worksheet_steps,
            'timing_summary': f'Total: {sum(s.get("duration_minutes", 5) for s in worksheet_steps)} minutes',
            'output_instructions': activity.get('expected_output', 'A shared group response document') if isinstance(activity, dict) else 'A shared group response document',
            'reporting_instructions': activity.get('reporting_instructions', 'Present key findings to the class') if isinstance(activity, dict) else 'Present key findings to the class',
        }

        slide_items = [
            {'slide_number': 1, 'title': 'Activity Overview', 'content': student_worksheet['goal']},
        ]
        for ws in worksheet_steps[:6]:
            slide_items.append({
                'slide_number': len(slide_items) + 1,
                'title': ws['title'],
                'content': ws.get('description', '') + (' (' + str(ws.get('duration_minutes', '')) + ' min)' if ws.get('duration_minutes') else ''),
            })
        slide_items.append({
            'slide_number': len(slide_items) + 1,
            'title': 'Expected Output',
            'content': student_worksheet['output_instructions'],
        })

        student_slides = {
            'title': student_worksheet['title'],
            'slides': slide_items,
        }

        teacher_guide = {
            'overview': activity.get('overview', f'A collaborative activity about {topic}') if isinstance(activity, dict) else f'A collaborative activity about {topic}',
            'alignment_with_objectives': 'This activity aligns with the stated learning objectives through structured group collaboration.',
            'rationale': 'Group work promotes deeper engagement with the material and develops collaborative skills.',
            'implementation_steps': 'Divide students into groups, distribute the worksheet, monitor progress, and facilitate debrief.',
            'monitoring_points': 'Check that all group members are participating. Listen for misconceptions during discussions.',
            'expected_difficulties': 'Students may struggle with time management or distributing work evenly among group members.',
            'debrief_questions': 'What was the most surprising finding? How did your group resolve disagreements?',
            'adaptation_suggestions': 'For larger classes, use jigsaw method. For online, use breakout rooms with shared docs.',
        }

        return {
            'success': True,
            'error': None,
            'provider': 'mock',
            'model': Config.MOCK_MODEL,
            'materials': {
                'roles': roles,
                'scenes': scenes,
                'student_worksheet': student_worksheet,
                'student_slides': student_slides,
                'teacher_guide': teacher_guide,
            }
        }


def _build_planner_system_prompt(teaching_stage: str, collaboration_purpose: str, group_size: int) -> str:
    return (
        "You are an expert CSCL (Computer-Supported Collaborative Learning) instructional designer "
        "grounded in Dillenbourg's scripting theory and the ArgCSCL argumentation framework.\n\n"
        "PEDAGOGICAL PRINCIPLES you MUST apply:\n"
        "1. Positive Interdependence — each student's contribution must be necessary for group success; the task CANNOT be completed by one person alone.\n"
        "2. Individual Accountability — each role has a unique deliverable that the group depends on.\n"
        "3. Promotive Interaction — design prompts that require students to build on each other's ideas (not just present independently).\n"
        "4. Scaffolded Argumentation — if debate/synthesis: follow Claim → Evidence → Counter → Synthesis structure.\n\n"
        "GROUNDING REQUIREMENT:\n"
        "If the payload includes 'retrieved_chunks' (course materials uploaded by the teacher), you MUST:\n"
        "- Reference specific concepts, examples, or data from these chunks in at least 2 activity steps.\n"
        "- Use phrases like 'Using the concept of [X] from the course materials...' in student prompts.\n"
        "- If no chunks are provided, design based on the topic and note 'No course documents were used for grounding.'\n\n"
        "Return ONLY valid JSON with a single top-level key 'activity'. The 'activity' object MUST contain:\n"
        "- 'title': string (short, specific activity title)\n"
        "- 'overview': string (1-2 sentences describing what the group will do)\n"
        "- 'objective': string (aligned with learning goals from the spec)\n"
        "- 'steps': array of 3-6 objects, each with: 'step_order' (int), 'title' (string), 'description' (string — detailed instructions, not vague), "
        "'duration_minutes' (int), 'prompts' (array of EXACT student-facing prompts — NOT 'discuss the topic' but specific like "
        "'Write a 3-sentence claim about [concept] supported by evidence from [specific course material]')\n"
        "- 'roles': array of objects, each with: 'role_name', 'description', 'responsibilities' (array). Empty array if role_structure is 'no_roles'.\n"
        "- 'expected_output': string (concrete deliverable the group must produce)\n"
        "- 'reporting_instructions': string (how to report back to class)\n\n"
        "IMPORTANT:\n"
        "- Do NOT generate a full lesson flow. Focus on ONE concrete group task.\n"
        f"- Teaching stage: {teaching_stage}. Collaboration purpose: {collaboration_purpose}. Design for groups of {group_size} students.\n"
        "- If the payload includes 'initial_idea', the teacher has given a free-text idea/preference; incorporate it.\n"
        "- All activities must be SELF-CONTAINED. Do NOT reference external images or figures not included in text.\n"
        "- Every prompt must be specific enough that a student can act on it WITHOUT asking the teacher for clarification."
    )


_MATERIAL_SYSTEM_PROMPT = (
    "You generate classroom-ready CSCL activity materials grounded in collaborative learning pedagogy. "
    "Return ONLY valid JSON with these keys:\n"
    "- roles (list of {role_name, description, responsibilities})\n"
    "- scenes (list of {order_index, scene_type, purpose, transition_rule, scriptlets: [{prompt_text, prompt_type, role_id}]})\n"
    "- student_worksheet: object with title, goal, roles_summary, "
    "steps (each with title, description AS FULL INSTRUCTIONS not summaries, duration_minutes, "
    "prompts AS EXACT STUDENT-FACING TEXT that students read and act on directly), "
    "timing_summary, output_instructions (what to produce), reporting_instructions\n"
    "- student_slides: {title, slides: [{slide_number, title, content}]} — 4-8 slides for projecting in class\n"
    "- teacher_guide: {overview, alignment_with_objectives, rationale, "
    "implementation_steps (step-by-step for the teacher), monitoring_points (what to watch for), "
    "expected_difficulties (common student struggles AND how to address each), "
    "debrief_questions, adaptation_suggestions}\n\n"
    "QUALITY REQUIREMENTS:\n"
    "- Student worksheet steps must be COMPLETE INSTRUCTIONS, not summaries. A student should be able to do the entire activity using ONLY the worksheet.\n"
    "- Each prompt must reference specific course concepts when retrieved_chunks are available.\n"
    "- Teacher guide must include concrete intervention strategies for each expected difficulty.\n"
    "- All materials must be SELF-CONTAINED. No references to external images or figures."
)


_CRITIC_REFINER_SYSTEM_PROMPT = (
    "You are a CSCL activity quality evaluator AND refiner. Perform TWO tasks in sequence:\n\n"
    "TASK 1 — EVALUATE: Check the materials against these criteria:\n"
    "1. Positive Interdependence: Can one student complete this alone? (If yes → issue)\n"
    "2. Specificity: Are prompts concrete enough that students can act without asking the teacher? (Vague prompts like 'discuss the topic' → issue)\n"
    "3. Course Grounding: Do at least 2 steps reference specific concepts from course materials? (If not → warning)\n"
    "4. Completeness: Does student_worksheet contain full instructions (not just titles)? Does teacher_guide include difficulty+intervention pairs?\n"
    "5. Structure: At least 1 scene/step with non-empty scriptlets or prompts.\n\n"
    "TASK 2 — REFINE: Fix ALL issues found. Improve vague prompts into specific ones. Add missing materials.\n\n"
    "Return ONLY JSON with keys:\n"
    "- validation: {is_valid: boolean, issues: [strings], warnings: [strings]}\n"
    "- quality_indicators: {scene_count, role_count, scriptlet_count}\n"
    "- roles: (refined list)\n"
    "- scenes: (refined list, each with scriptlets)\n"
    "- refinements_applied: {scenes_added, roles_added, scriptlets_fixed, prompts_made_specific, grounding_added}\n"
    "- student_worksheet: (refined, with FULL instructions in each step)\n"
    "- student_slides: (refined)\n"
    "- teacher_guide: (refined, with expected_difficulties containing problem+solution pairs)"
)


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
        base_url = (str(_get_config_value('OPENAI_BASE_URL', 'https://api.openai.com/v1')).strip() or 'https://api.openai.com/v1').rstrip('/')
        timeout_s = int(_as_int(_get_config_value('OPENAI_TIMEOUT_SECONDS', 120), 120))
        max_retries = int(_as_int(_get_config_value('OPENAI_MAX_RETRIES', 1), 1))

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
            teaching_stage = input_payload.get('teaching_stage') or 'concept_exploration'
            collaboration_purpose = input_payload.get('collaboration_purpose') or 'compare_ideas'
            group_size = input_payload.get('group_size') or 4
            user_text = json.dumps(input_payload, ensure_ascii=False)
            system_prompt = _build_planner_system_prompt(teaching_stage, collaboration_purpose, group_size)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Design one CSCL group activity from this specification. Return JSON with key 'activity' only.\n\n{user_text}"}
            ]

            resp, req_error = _post_json_with_retry(
                url=f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                payload={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            if req_error:
                return {
                    'success': False,
                    'plan': None,
                    'error': f"OpenAI request failed: {req_error}",
                    'provider': 'openai',
                    'model': model
                }

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
        base_url = (str(_get_config_value('OPENAI_BASE_URL', 'https://api.openai.com/v1')).strip() or 'https://api.openai.com/v1').rstrip('/')
        timeout_s = int(_as_int(_get_config_value('OPENAI_TIMEOUT_SECONDS', 120), 120))
        max_retries = int(_as_int(_get_config_value('OPENAI_MAX_RETRIES', 1), 1))

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

            resp, req_error = _post_json_with_retry(
                url=f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                payload={"model": model, "messages": messages, "temperature": 0, "max_tokens": 4096},
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            if req_error:
                return {
                    'success': False,
                    'error': f"OpenAI request failed: {req_error}",
                    'provider': 'openai',
                    'model': model,
                    'output': None
                }

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
        r = self._chat_json(_MATERIAL_SYSTEM_PROMPT, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'materials': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'materials': out}

    def critique_and_refine(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self._chat_json(_CRITIC_REFINER_SYSTEM_PROMPT, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'result': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'result': out}

    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.critique_and_refine(input_payload)
        return {'success': r['success'], 'error': r.get('error'), 'provider': r['provider'], 'model': r['model'], 'critique': r.get('result')}

    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.critique_and_refine(input_payload)
        return {'success': r['success'], 'error': r.get('error'), 'provider': r['provider'], 'model': r['model'], 'refined': r.get('result')}


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
        max_retries = int(_as_int(_get_config_value('QWEN_MAX_RETRIES', 1), 1))

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
            teaching_stage = input_payload.get('teaching_stage') or 'concept_exploration'
            collaboration_purpose = input_payload.get('collaboration_purpose') or 'compare_ideas'
            group_size = input_payload.get('group_size') or 4
            messages = [
                {"role": "system", "content": _build_planner_system_prompt(teaching_stage, collaboration_purpose, group_size)},
                {"role": "user", "content": f"Design one CSCL group activity from this specification. Return JSON with key 'activity' only.\n\n{user_text}"}
            ]

            resp, req_error = _post_json_with_retry(
                url=f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                payload={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3
                },
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            if req_error:
                return {
                    'success': False,
                    'plan': None,
                    'error': f"Qwen request failed: {req_error}",
                    'provider': 'qwen',
                    'model': model
                }

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
    
    def _qwen_chat_json(self, system_prompt: str, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic Qwen chat JSON call (mirrors OpenAI._chat_json)"""
        model = str(_get_config_value('QWEN_MODEL', 'qwen-plus'))
        base_url = str(_get_config_value('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')).rstrip('/')
        timeout_s = int(_as_int(_get_config_value('QWEN_TIMEOUT_SECONDS', 120), 120))
        max_retries = int(_as_int(_get_config_value('QWEN_MAX_RETRIES', 1), 1))
        api_key = (
            os.getenv('QWEN_API_KEY', '') or str(_get_config_value('QWEN_API_KEY', '')) or
            os.getenv('DASHSCOPE_API_KEY', '') or str(_get_config_value('DASHSCOPE_API_KEY', ''))
        )
        if not api_key or not str(api_key).strip():
            return {'success': False, 'error': 'QWEN_API_KEY not configured', 'provider': 'qwen', 'model': model, 'output': None}
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
            ]
            resp, req_error = _post_json_with_retry(
                url=f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                payload={"model": model, "messages": messages, "temperature": 0, "max_tokens": 4096},
                timeout_s=timeout_s,
                max_retries=max_retries,
            )
            if req_error:
                return {'success': False, 'error': f"Qwen request failed: {req_error}", 'provider': 'qwen', 'model': model, 'output': None}
            if resp.status_code >= 400:
                return {'success': False, 'error': f"Qwen API HTTP {resp.status_code}: {(resp.text or '')[:500]}", 'provider': 'qwen', 'model': model, 'output': None}
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return {'success': False, 'error': 'Qwen API returned empty content', 'provider': 'qwen', 'model': model, 'output': None}
            try:
                parsed = json.loads(content)
            except Exception:
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
            return {'success': True, 'error': None, 'provider': 'qwen', 'model': model, 'output': parsed}
        except Exception as e:
            return {'success': False, 'error': f"Qwen request failed: {type(e).__name__}: {e}", 'provider': 'qwen', 'model': model, 'output': None}

    def generate_materials(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self._qwen_chat_json(_MATERIAL_SYSTEM_PROMPT, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'materials': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'materials': out}

    def critique_and_refine(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self._qwen_chat_json(_CRITIC_REFINER_SYSTEM_PROMPT, input_payload)
        if not r['success']:
            return {'success': False, 'error': r['error'], 'provider': r['provider'], 'model': r['model'], 'result': None}
        out = r['output'] or {}
        return {'success': True, 'error': None, 'provider': r['provider'], 'model': r['model'], 'result': out}

    def critique_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.critique_and_refine(input_payload)
        return {'success': r['success'], 'error': r.get('error'), 'provider': r['provider'], 'model': r['model'], 'critique': r.get('result')}

    def refine_script(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.critique_and_refine(input_payload)
        return {'success': r['success'], 'error': r.get('error'), 'provider': r['provider'], 'model': r['model'], 'refined': r.get('result')}


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

    def critique_and_refine(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback('critique_and_refine', input_payload)


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
