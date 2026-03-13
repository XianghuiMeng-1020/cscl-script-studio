"""Map teacher-facing collaboration purpose to internal task_type and infer expected_output.
Frontend shows only Collaboration purpose; task_type is derived here for pipeline/validator.
Also maps 5 high-level teaching_stage values to granular stages for config compatibility.
"""
from typing import Dict, Any, List

# 5 high-level teaching stages (UI) -> granular stage ids used in config/task_types.json compatible_teaching_stages
TEACHING_STAGE_TO_GRANULAR: Dict[str, List[str]] = {
    'warm_up': ['warm_up'],
    'concept_exploration': ['concept_exploration'],
    'practice_application': ['guided_practice', 'application'],
    'sharing_synthesis': ['discussion', 'synthesis'],
    'reflection_evaluation': ['reflection', 'assessment_prep'],
    # Legacy granular values pass through as single-element list
    'guided_practice': ['guided_practice'],
    'application': ['application'],
    'discussion': ['discussion'],
    'synthesis': ['synthesis'],
    'reflection': ['reflection'],
    'assessment_prep': ['assessment_prep'],
    'other': ['concept_exploration'],
}


def teaching_stage_to_compatible_list(teaching_stage: str) -> List[str]:
    """Return list of granular stage ids for compatibility checks with task_types.json."""
    key = (teaching_stage or '').strip().lower()
    return TEACHING_STAGE_TO_GRANULAR.get(key, ['concept_exploration'])

# New (simplified) and legacy purpose ids -> internal task_type id (must exist in config/task_types.json)
PURPOSE_TO_TASK_TYPE: Dict[str, str] = {
    # New 6-option UI values
    'compare_discuss_ideas': 'structured_debate',
    'interpret_evidence_solve_problem': 'evidence_comparison',
    'build_shared_explanation_product': 'perspective_synthesis',
    'critique_improve_work': 'peer_review',
    'reach_consensus_decision': 'case_analysis',
    'other': 'structured_debate',
    # Legacy purpose ids (for backward compatibility)
    'compare_ideas': 'structured_debate',
    'interpret_evidence': 'evidence_comparison',
    'build_consensus': 'case_analysis',
    'critique_alternatives': 'peer_review',
    'co_construct_explanation': 'perspective_synthesis',
    'collaborative_problem_solving': 'problem_based_learning',
    'peer_review': 'peer_review',
    'create_shared_product': 'perspective_synthesis',
}

DEFAULT_TASK_TYPE = 'structured_debate'


def purpose_to_task_type(collaboration_purpose: str) -> str:
    """Map collaboration purpose to internal task_type for pipeline/templates."""
    if not collaboration_purpose or not collaboration_purpose.strip():
        return DEFAULT_TASK_TYPE
    key = (collaboration_purpose or '').strip().lower()
    return PURPOSE_TO_TASK_TYPE.get(key, DEFAULT_TASK_TYPE)


def infer_expected_output(spec: Dict[str, Any]) -> str:
    """Infer a short expected-output description when teacher does not provide one.
    Uses collaboration_purpose, learning_objectives, and duration for a simple template.
    """
    purpose = (spec.get('collaboration_purpose') or '').strip().lower()
    tr = spec.get('task_requirements') or {}
    existing = (tr.get('expected_output') or '').strip()
    if existing:
        return existing

    # Simple template by purpose (English; can be localized later)
    templates = {
        'compare_discuss_ideas': 'Group argument map or position summary with evidence',
        'interpret_evidence_solve_problem': 'Shared analysis or solution with justified conclusions',
        'build_shared_explanation_product': 'Shared explanation or joint product (e.g. document, poster)',
        'critique_improve_work': 'Revised work with peer feedback summary',
        'reach_consensus_decision': 'Group decision or consensus statement with rationale',
        'other': 'Group artifact (e.g. summary, list, or short report)',
        # Legacy
        'compare_ideas': 'Group argument map or position summary with evidence',
        'interpret_evidence': 'Shared analysis or solution with justified conclusions',
        'build_consensus': 'Group decision or consensus statement with rationale',
        'critique_alternatives': 'Revised work with peer feedback summary',
        'co_construct_explanation': 'Shared explanation or joint product',
        'collaborative_problem_solving': 'Shared solution or recommendation',
        'peer_review': 'Revised work with peer feedback summary',
        'create_shared_product': 'Shared explanation or joint product',
    }
    return templates.get(purpose, 'Group artifact (e.g. shared summary or decision)')


def ensure_spec_has_task_type_and_expected_output(spec_data: Dict[str, Any]) -> None:
    """Mutate spec_data in place: set task_requirements.task_type from purpose if missing;
    set task_requirements.expected_output from infer_expected_output if missing.
    """
    tr = spec_data.setdefault('task_requirements', {})
    if not (tr.get('task_type') or '').strip():
        tr['task_type'] = purpose_to_task_type(spec_data.get('collaboration_purpose', ''))
    if not (tr.get('expected_output') or '').strip():
        tr['expected_output'] = infer_expected_output(spec_data)
