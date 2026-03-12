"""Pedagogical specification validator"""
from typing import Dict, List, Any, Optional
from app.schemas.pedagogical_spec import (
    PedagogicalSpec, CourseContext, LearningObjectives,
    TaskRequirements, Constraints, RubricPreferences
)
from app.services.task_type_config import get_valid_task_type_ids


class SpecValidationError(Exception):
    """Custom exception for spec validation errors"""
    pass


class SpecValidator:
    """Validator for pedagogical specifications"""
    
    REQUIRED_FIELDS = {
        'course_context': ['subject', 'topic', 'class_size', 'mode', 'duration', 'description'],
        'learning_objectives': ['knowledge', 'skills'],
        'task_requirements': ['task_type', 'expected_output', 'collaboration_form', 'requirements_text']
    }
    
    VALID_MODES = ['sync', 'async']
    # Deprecated: use get_valid_task_type_ids() only. Kept as comment for fallback reference.
    # VALID_TASK_TYPES = ['debate', 'collaborative_synthesis', 'collaborative_writing', ...]
    VALID_COLLABORATION_FORMS = ['group', 'pair', 'individual_with_sharing', 'whole_class']
    
    @staticmethod
    def validate(spec_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pedagogical specification
        
        Args:
            spec_data: Raw specification data dictionary
            
        Returns:
            {
                'valid': bool,
                'issues': List[str],
                'normalized_spec': Optional[Dict]  # Only if valid
            }
        """
        issues: List[str] = []
        field_paths: List[str] = []  # machine-readable paths for frontend (same order as issues)

        def add(msg: str, path: str) -> None:
            issues.append(msg)
            field_paths.append(path)

        # Check required top-level fields
        if 'course_context' not in spec_data:
            add('Missing required field: course_context', 'course_context')
        if 'learning_objectives' not in spec_data:
            add('Missing required field: learning_objectives', 'learning_objectives')
        if 'task_requirements' not in spec_data:
            add('Missing required field: task_requirements', 'task_requirements')

        if issues:
            return {
                'valid': False,
                'issues': issues,
                'field_paths': field_paths,
                'normalized_spec': None
            }

        # Validate course_context
        course_context = spec_data.get('course_context', {})
        for msg, path in SpecValidator._validate_course_context(course_context):
            add(msg, path)

        # Validate learning_objectives
        learning_objectives = spec_data.get('learning_objectives', {})
        for msg, path in SpecValidator._validate_learning_objectives(learning_objectives):
            add(msg, path)

        # Validate task_requirements
        task_requirements = spec_data.get('task_requirements', {})
        for msg, path in SpecValidator._validate_task_requirements(task_requirements):
            add(msg, path)

        # Validate optional fields if present (no field_paths for optional)
        if 'constraints' in spec_data:
            for msg in SpecValidator._validate_constraints(spec_data['constraints']):
                issues.append(msg)
        if 'rubric_preferences' in spec_data:
            for msg in SpecValidator._validate_rubric_preferences(spec_data['rubric_preferences']):
                issues.append(msg)

        # If there are issues, return invalid
        if issues:
            return {
                'valid': False,
                'issues': issues,
                'field_paths': field_paths,
                'normalized_spec': None
            }

        # Try to create normalized spec
        try:
            spec = PedagogicalSpec.from_dict(spec_data)
            normalized_spec = spec.to_dict()
        except Exception as e:
            issues.append(f'Failed to normalize spec: {str(e)}')
            field_paths.append('spec')
            return {
                'valid': False,
                'issues': issues,
                'field_paths': field_paths,
                'normalized_spec': None
            }

        # Alignment checks (warnings only, do not invalidate)
        warnings = SpecValidator._check_alignment(normalized_spec)

        return {
            'valid': True,
            'issues': [],
            'field_paths': [],
            'normalized_spec': normalized_spec,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_course_context(context: Dict[str, Any]) -> List[tuple]:
        """Validate course context. Returns list of (message, field_path)."""
        out: List[tuple] = []
        path = 'course_context'
        if 'subject' not in context or not context['subject']:
            out.append(('course_context.subject is required and cannot be empty', f'{path}.subject'))
        if 'topic' not in context or not context['topic']:
            out.append(('course_context.topic is required and cannot be empty', f'{path}.topic'))
        if 'class_size' not in context:
            out.append(('course_context.class_size is required', f'{path}.class_size'))
        elif not isinstance(context['class_size'], int) or context['class_size'] <= 0:
            out.append(('course_context.class_size must be a positive integer', f'{path}.class_size'))
        if 'mode' not in context:
            out.append(('course_context.mode is required', f'{path}.mode'))
        elif context['mode'] not in SpecValidator.VALID_MODES:
            out.append((f'course_context.mode must be one of: {", ".join(SpecValidator.VALID_MODES)}', f'{path}.mode'))
        if 'duration' not in context:
            out.append(('course_context.duration is required', f'{path}.duration'))
        elif not isinstance(context['duration'], int) or context['duration'] <= 0:
            out.append(('course_context.duration must be a positive integer', f'{path}.duration'))
        if 'description' not in context or not (context.get('description') or '').strip():
            out.append(('course_context.description is required and cannot be empty', f'{path}.description'))
        return out
    
    @staticmethod
    def _validate_learning_objectives(objectives: Dict[str, Any]) -> List[tuple]:
        """Validate learning objectives. Returns list of (message, field_path)."""
        out: List[tuple] = []
        path = 'learning_objectives'
        if 'knowledge' not in objectives:
            out.append(('learning_objectives.knowledge is required', f'{path}.knowledge'))
        elif not isinstance(objectives['knowledge'], list):
            out.append(('learning_objectives.knowledge must be a list', f'{path}.knowledge'))
        elif len(objectives['knowledge']) == 0:
            out.append(('learning_objectives.knowledge must contain at least one objective', f'{path}.knowledge'))
        if 'skills' not in objectives:
            out.append(('learning_objectives.skills is required', f'{path}.skills'))
        elif not isinstance(objectives['skills'], list):
            out.append(('learning_objectives.skills must be a list', f'{path}.skills'))
        elif len(objectives['skills']) == 0:
            out.append(('learning_objectives.skills must contain at least one objective', f'{path}.skills'))
        if 'disposition' in objectives and not isinstance(objectives['disposition'], list):
            out.append(('learning_objectives.disposition must be a list if provided', f'{path}.disposition'))
        return out
    
    @staticmethod
    def _validate_task_requirements(requirements: Dict[str, Any]) -> List[tuple]:
        """Validate task requirements. Returns list of (message, field_path)."""
        out: List[tuple] = []
        path = 'task_requirements'
        valid_ids = get_valid_task_type_ids()
        if 'task_type' not in requirements or not requirements['task_type']:
            out.append(('task_requirements.task_type is required and cannot be empty', f'{path}.task_type'))
        elif requirements['task_type'] not in valid_ids:
            out.append((f'task_requirements.task_type must be one of: {", ".join(valid_ids)}', f'{path}.task_type'))
        if 'expected_output' not in requirements or not requirements['expected_output']:
            out.append(('task_requirements.expected_output is required and cannot be empty', f'{path}.expected_output'))
        if 'collaboration_form' not in requirements:
            out.append(('task_requirements.collaboration_form is required', f'{path}.collaboration_form'))
        elif requirements['collaboration_form'] not in SpecValidator.VALID_COLLABORATION_FORMS:
            out.append((f'task_requirements.collaboration_form must be one of: {", ".join(SpecValidator.VALID_COLLABORATION_FORMS)}', f'{path}.collaboration_form'))
        if 'requirements_text' not in requirements or not (requirements.get('requirements_text') or '').strip():
            out.append(('task_requirements.requirements_text is required and cannot be empty', f'{path}.requirements_text'))
        return out
    
    @staticmethod
    def _validate_constraints(constraints: Dict[str, Any]) -> List[str]:
        """Validate constraints (optional field). Returns list of messages only (no field_paths)."""
        issues = []
        if 'tools' in constraints and not isinstance(constraints['tools'], list):
            issues.append('constraints.tools must be a list if provided')
        if 'timebox' in constraints and constraints['timebox'] is not None:
            if not isinstance(constraints['timebox'], int) or constraints['timebox'] <= 0:
                issues.append('constraints.timebox must be a positive integer if provided')
        return issues

    @staticmethod
    def _validate_rubric_preferences(preferences: Dict[str, Any]) -> List[str]:
        """Validate rubric preferences (optional field). Returns list of messages only."""
        issues = []
        if 'criteria' in preferences and not isinstance(preferences['criteria'], list):
            issues.append('rubric_preferences.criteria must be a list if provided')
        if 'weight' in preferences and preferences['weight'] is not None:
            if not isinstance(preferences['weight'], dict):
                issues.append('rubric_preferences.weight must be a dictionary if provided')
        return issues

    @staticmethod
    def _check_alignment(spec: Dict[str, Any]) -> List[str]:
        """Check alignment across topic, task_type, learning objectives, expected_output, collaboration. Returns list of warning messages (does not invalidate)."""
        warnings: List[str] = []
        tr = spec.get('task_requirements') or {}
        task_type = tr.get('task_type') or ''
        expected_output = (tr.get('expected_output') or '').strip()
        collaboration_form = tr.get('collaboration_form') or 'group'
        teaching_stage = spec.get('teaching_stage') or ''
        collaboration_purpose = spec.get('collaboration_purpose') or ''
        group_size = spec.get('group_size')
        cc = spec.get('course_context') or {}
        class_size = cc.get('class_size') or 0

        if collaboration_form == 'pair' and group_size and group_size != 2:
            warnings.append('Collaboration form is "pair" but group size is not 2; consider setting group size to 2.')
        if collaboration_form == 'whole_class' and group_size and group_size > 1:
            warnings.append('Collaboration form is "whole class"; group size may be ignored.')
        if group_size is not None and class_size > 0 and group_size > 0 and class_size % group_size != 0:
            warnings.append('Class size is not evenly divisible by group size; some students may need to join other groups or work individually.')
        if teaching_stage == 'warm_up' and task_type in ('structured_debate', 'evidence_comparison'):
            warnings.append('Warm-up stage often suits lighter tasks; structured debate/evidence comparison may be better for concept exploration or application.')
        if collaboration_purpose == 'peer_review' and task_type not in ('peer_review', 'evidence_comparison', 'perspective_synthesis'):
            warnings.append('Collaboration purpose is peer review; consider choosing a task type that supports peer review (e.g. peer_review, evidence_comparison).')
        return warnings
