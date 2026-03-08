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
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'knowledge': self.knowledge,
            'skills': self.skills
        }
        if self.disposition:
            result['disposition'] = self.disposition
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningObjectives':
        return cls(
            knowledge=data.get('knowledge', []),
            skills=data.get('skills', []),
            disposition=data.get('disposition', [])
        )


@dataclass
class TaskRequirements:
    """Task requirements specification (proposal-aligned: collaboration and evidence requirements)."""
    task_type: str  # e.g., "debate", "collaborative_synthesis", "jigsaw", "role_play"
    expected_output: str  # Description of expected output
    collaboration_form: str  # e.g., "group", "pair", "individual_with_sharing"
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
            task_type=data.get('task_type', ''),
            expected_output=data.get('expected_output', ''),
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
    diversity_considerations: Optional[str] = None  # Diversity/accessibility notes
    accessibility_considerations: Optional[str] = None  # Accessibility notes
    
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
        if self.diversity_considerations:
            result['diversity_considerations'] = self.diversity_considerations
        if self.accessibility_considerations:
            result['accessibility_considerations'] = self.accessibility_considerations
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PedagogicalSpec':
        return cls(
            course_context=CourseContext.from_dict(data.get('course_context', {})),
            learning_objectives=LearningObjectives.from_dict(data.get('learning_objectives', {})),
            task_requirements=TaskRequirements.from_dict(data.get('task_requirements', {})),
            constraints=Constraints.from_dict(data.get('constraints', {})) if data.get('constraints') else None,
            rubric_preferences=RubricPreferences.from_dict(data.get('rubric_preferences', {})) if data.get('rubric_preferences') else None,
            diversity_considerations=data.get('diversity_considerations'),
            accessibility_considerations=data.get('accessibility_considerations')
        )
