"""Pedagogical specification schema definitions"""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class CourseContext:
    """Course context specification (proposal-aligned: setting, learner profile, instructional context)."""
    subject: str  # e.g., "Data Science", "Learning Sciences" (course name)
    topic: str  # Specific topic within the subject
    class_size: int  # Number of students
    mode: str  # "sync" or "async"
    duration: int  # Duration in minutes
    description: str = ''  # Course setting, learner profile, instructional context (required for validation)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'subject': self.subject,
            'topic': self.topic,
            'class_size': self.class_size,
            'mode': self.mode,
            'duration': self.duration,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CourseContext':
        return cls(
            subject=data.get('subject', ''),
            topic=data.get('topic', ''),
            class_size=data.get('class_size', 0),
            mode=data.get('mode', 'sync'),
            duration=data.get('duration', 60),
            description=data.get('description', '')
        )


@dataclass
class LearningObjectives:
    """Learning objectives specification"""
    knowledge: List[str] = field(default_factory=list)  # Knowledge objectives
    skills: List[str] = field(default_factory=list)  # Skill objectives
    disposition: List[str] = field(default_factory=list)  # Disposition objectives (optional)
    collaboration_objectives: List[str] = field(default_factory=list)  # CSCL collaboration objectives (optional)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'knowledge': self.knowledge,
            'skills': self.skills
        }
        if self.disposition:
            result['disposition'] = self.disposition
        if self.collaboration_objectives:
            result['collaboration_objectives'] = self.collaboration_objectives
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningObjectives':
        return cls(
            knowledge=data.get('knowledge', []),
            skills=data.get('skills', []),
            disposition=data.get('disposition', []),
            collaboration_objectives=data.get('collaboration_objectives', [])
        )


@dataclass
class ActivityDesign:
    """Activity-level design: teaching stage, collaboration purpose, group config."""
    teaching_stage: str = 'concept_exploration'  # warm_up, concept_exploration, practice_application, sharing_synthesis, reflection_evaluation (5 high-level)
    collaboration_purpose: str = 'compare_ideas'  # compare_discuss_ideas, interpret_evidence_solve_problem, build_shared_explanation_product, critique_improve_work, reach_consensus_decision, other (6 options); legacy ids supported
    group_size: int = 4
    grouping_strategy: str = 'random'  # random, teacher_assigned, self_selected (3 options)
    role_structure: str = 'no_roles'  # no_roles, assigned_roles, rotating_roles, self_selected_roles
    whole_class_reporting: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'teaching_stage': self.teaching_stage,
            'collaboration_purpose': self.collaboration_purpose,
            'group_size': self.group_size,
            'grouping_strategy': self.grouping_strategy,
            'role_structure': self.role_structure,
            'whole_class_reporting': self.whole_class_reporting
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityDesign':
        return cls(
            teaching_stage=data.get('teaching_stage', 'concept_exploration'),
            collaboration_purpose=data.get('collaboration_purpose', 'compare_ideas'),
            group_size=int(data.get('group_size', 4)) if data.get('group_size') is not None else 4,
            grouping_strategy=data.get('grouping_strategy', 'random'),
            role_structure=data.get('role_structure', 'no_roles'),
            whole_class_reporting=data.get('whole_class_reporting', True)
        )


@dataclass
class ScaffoldingPreferences:
    """Scaffolding and teacher-concern preferences."""
    scaffolding_options: List[str] = field(default_factory=list)  # role_cards, sentence_starters, worksheet_prompts, discussion_stems, timing_guidance, reporting_templates, teacher_facilitation_cues
    student_difficulties: str = ''  # What students usually struggle with
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'scaffolding_options': self.scaffolding_options}
        if self.student_difficulties:
            result['student_difficulties'] = self.student_difficulties
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScaffoldingPreferences':
        return cls(
            scaffolding_options=data.get('scaffolding_options', []) or [],
            student_difficulties=data.get('student_difficulties', '') or ''
        )


@dataclass
class OutputPreferences:
    """Preferred output artefact formats."""
    output_formats: List[str] = field(default_factory=lambda: ['student_worksheet', 'teacher_facilitation_sheet'])  # student_worksheet, student_slides, teacher_facilitation_sheet, full_package
    
    def to_dict(self) -> Dict[str, Any]:
        return {'output_formats': self.output_formats}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutputPreferences':
        formats = data.get('output_format') or data.get('output_formats') or ['student_worksheet', 'teacher_facilitation_sheet']
        return cls(output_formats=list(formats) if isinstance(formats, (list, tuple)) else [formats])


@dataclass
class TaskRequirements:
    """Task requirements specification (proposal-aligned: collaboration and evidence requirements)."""
    task_type: str  # Derived from collaboration_purpose if not provided; e.g. "structured_debate", "evidence_comparison"
    expected_output: str = ''  # Optional; inferred from purpose/objectives if empty
    collaboration_form: str = 'group'  # e.g., "group", "pair", "individual_with_sharing"
    requirements_text: str = ''  # Concrete collaboration/evidence requirements (required for validation)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_type': self.task_type,
            'expected_output': self.expected_output,
            'collaboration_form': self.collaboration_form,
            'requirements_text': self.requirements_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskRequirements':
        return cls(
            task_type=data.get('task_type', '') or 'structured_debate',
            expected_output=(data.get('expected_output') or '').strip(),
            collaboration_form=data.get('collaboration_form', 'group'),
            requirements_text=data.get('requirements_text', '')
        )


@dataclass
class Constraints:
    """Constraints specification (optional)"""
    tools: List[str] = field(default_factory=list)  # Available tools
    timebox: Optional[int] = None  # Time constraint in minutes
    assessment_constraints: Optional[str] = None  # Assessment-related constraints
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools:
            result['tools'] = self.tools
        if self.timebox:
            result['timebox'] = self.timebox
        if self.assessment_constraints:
            result['assessment_constraints'] = self.assessment_constraints
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Constraints':
        return cls(
            tools=data.get('tools', []),
            timebox=data.get('timebox'),
            assessment_constraints=data.get('assessment_constraints')
        )


@dataclass
class RubricPreferences:
    """Rubric preferences specification (optional)"""
    criteria: List[str] = field(default_factory=list)  # Criteria names
    weight: Optional[Dict[str, float]] = None  # Weight mapping (optional)
    emphasis: Optional[str] = None  # Emphasis description
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.criteria:
            result['criteria'] = self.criteria
        if self.weight:
            result['weight'] = self.weight
        if self.emphasis:
            result['emphasis'] = self.emphasis
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RubricPreferences':
        return cls(
            criteria=data.get('criteria', []),
            weight=data.get('weight'),
            emphasis=data.get('emphasis')
        )


@dataclass
class PedagogicalSpec:
    """Complete pedagogical specification"""
    course_context: CourseContext
    learning_objectives: LearningObjectives
    task_requirements: TaskRequirements
    constraints: Optional[Constraints] = None
    rubric_preferences: Optional[RubricPreferences] = None
    activity_design: Optional[ActivityDesign] = None
    scaffolding_preferences: Optional[ScaffoldingPreferences] = None
    output_preferences: Optional[OutputPreferences] = None
    diversity_considerations: Optional[str] = None
    accessibility_considerations: Optional[str] = None
    initial_idea: Optional[str] = None  # Teacher's optional free-text idea/preference for the activity
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'course_context': self.course_context.to_dict(),
            'learning_objectives': self.learning_objectives.to_dict(),
            'task_requirements': self.task_requirements.to_dict()
        }
        if self.constraints:
            result['constraints'] = self.constraints.to_dict()
        if self.rubric_preferences:
            result['rubric_preferences'] = self.rubric_preferences.to_dict()
        if self.activity_design:
            result['activity_design'] = self.activity_design.to_dict()
            result['teaching_stage'] = self.activity_design.teaching_stage
            result['collaboration_purpose'] = self.activity_design.collaboration_purpose
            result['group_size'] = self.activity_design.group_size
            result['grouping_strategy'] = self.activity_design.grouping_strategy
            result['role_structure'] = self.activity_design.role_structure
            result['whole_class_reporting'] = self.activity_design.whole_class_reporting
        if self.scaffolding_preferences:
            result['scaffolding_preferences'] = self.scaffolding_preferences.to_dict()
            result['scaffolding_options'] = self.scaffolding_preferences.scaffolding_options
            result['student_difficulties'] = self.scaffolding_preferences.student_difficulties
        if self.output_preferences:
            result['output_preferences'] = self.output_preferences.to_dict()
            result['output_format'] = self.output_preferences.output_formats
        if self.diversity_considerations:
            result['diversity_considerations'] = self.diversity_considerations
        if self.accessibility_considerations:
            result['accessibility_considerations'] = self.accessibility_considerations
        if self.initial_idea:
            result['initial_idea'] = self.initial_idea
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PedagogicalSpec':
        activity_design = None
        ad_data = data.get('activity_design') or {}
        if data.get('teaching_stage') is not None:
            ad_data = {**ad_data, 'teaching_stage': data.get('teaching_stage'), 'collaboration_purpose': data.get('collaboration_purpose', 'compare_ideas'),
                'group_size': data.get('group_size', 4), 'grouping_strategy': data.get('grouping_strategy', 'random'),
                'role_structure': data.get('role_structure', 'no_roles'), 'whole_class_reporting': data.get('whole_class_reporting', True)}
        if ad_data or data.get('teaching_stage') is not None:
            activity_design = ActivityDesign.from_dict(ad_data)
        scaffolding_preferences = None
        sp_data = data.get('scaffolding_preferences') or {}
        if data.get('scaffolding_options') is not None:
            sp_data = {**sp_data, 'scaffolding_options': data.get('scaffolding_options', []), 'student_difficulties': data.get('student_difficulties', '')}
        if sp_data or data.get('scaffolding_options') is not None or data.get('student_difficulties'):
            scaffolding_preferences = ScaffoldingPreferences.from_dict(sp_data)
        output_preferences = None
        if data.get('output_format') is not None or data.get('output_preferences'):
            output_preferences = OutputPreferences.from_dict(data.get('output_preferences') or {'output_format': data.get('output_format')})
        return cls(
            course_context=CourseContext.from_dict(data.get('course_context', {})),
            learning_objectives=LearningObjectives.from_dict(data.get('learning_objectives', {})),
            task_requirements=TaskRequirements.from_dict(data.get('task_requirements', {})),
            constraints=Constraints.from_dict(data.get('constraints', {})) if data.get('constraints') else None,
            rubric_preferences=RubricPreferences.from_dict(data.get('rubric_preferences', {})) if data.get('rubric_preferences') else None,
            activity_design=activity_design,
            scaffolding_preferences=scaffolding_preferences,
            output_preferences=output_preferences,
            diversity_considerations=data.get('diversity_considerations'),
            accessibility_considerations=data.get('accessibility_considerations'),
            initial_idea=(data.get('initial_idea') or '').strip() or None
        )
