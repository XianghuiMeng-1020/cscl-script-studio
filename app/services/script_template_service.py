"""Script template service for generating CSCL script structures"""
from typing import List, Dict, Any
from datetime import datetime


class ScriptTemplateService:
    """Service for generating CSCL script templates using deterministic rules"""
    
    DEFAULT_SCENES = [
        {'type': 'opening', 'order': 1, 'purpose': 'Introduce topic and establish initial positions'},
        {'type': 'confrontation', 'order': 2, 'purpose': 'Present conflicting viewpoints and evidence'},
        {'type': 'argumentation', 'order': 3, 'purpose': 'Develop arguments and counterarguments'},
        {'type': 'conclusion', 'order': 4, 'purpose': 'Synthesize findings and reach consensus'}
    ]
    
    DEFAULT_ROLES = [
        {'name': 'advocate', 'responsibilities': ['Present initial position', 'Defend arguments']},
        {'name': 'challenger', 'responsibilities': ['Question assumptions', 'Present counterarguments']},
        {'name': 'synthesizer', 'responsibilities': ['Integrate perspectives', 'Identify common ground']},
        {'name': 'evidence_checker', 'responsibilities': ['Verify claims', 'Evaluate sources']}
    ]
    
    @staticmethod
    def generate_template(topic: str, objectives: List[str], duration_minutes: int, task_type: str) -> Dict[str, Any]:
        """Generate a CSCL script template using deterministic rules"""
        
        # Calculate scene duration (distribute time across scenes)
        num_scenes = len(ScriptTemplateService.DEFAULT_SCENES)
        scene_duration = duration_minutes // num_scenes
        
        # Generate scenes
        scenes = []
        for scene_def in ScriptTemplateService.DEFAULT_SCENES:
            scene = {
                'order_index': scene_def['order'],
                'scene_type': scene_def['type'],
                'purpose': f"{scene_def['purpose']} for topic: {topic}",
                'transition_rule': ScriptTemplateService._generate_transition_rule(scene_def['type']),
                'scriptlets': ScriptTemplateService._generate_scene_scriptlets(
                    scene_def['type'], 
                    topic, 
                    objectives,
                    scene_duration
                )
            }
            scenes.append(scene)
        
        # Generate roles (2-4 roles based on task type)
        num_roles = 4 if task_type in ('debate', 'structured_debate') else 2
        roles = []
        for i, role_def in enumerate(ScriptTemplateService.DEFAULT_ROLES[:num_roles]):
            role = {
                'role_name': role_def['name'],
                'responsibilities': [
                    f"{resp} related to {topic}" 
                    for resp in role_def['responsibilities']
                ]
            }
            roles.append(role)
        
        return {
            'scenes': scenes,
            'roles': roles
        }
    
    @staticmethod
    def _generate_transition_rule(scene_type: str) -> str:
        """Generate transition rule for scene type"""
        rules = {
            'opening': 'Move to confrontation when all participants have stated initial positions',
            'confrontation': 'Proceed to argumentation when key conflicts are identified',
            'argumentation': 'Advance to conclusion when arguments are sufficiently developed',
            'conclusion': 'End script when synthesis is complete'
        }
        return rules.get(scene_type, 'Continue based on group progress')
    
    @staticmethod
    def _generate_scene_scriptlets(scene_type: str, topic: str, objectives: List[str], duration: int) -> List[Dict[str, Any]]:
        """Generate scriptlets for a scene"""
        scriptlets = []
        
        if scene_type == 'opening':
            scriptlets.extend([
                {
                    'prompt_text': f'Introduce yourself and state your initial position on: {topic}',
                    'prompt_type': 'claim',
                    'role_id': None
                },
                {
                    'prompt_text': f'Share one learning objective you hope to achieve: {objectives[0] if objectives else "understanding the topic"}',
                    'prompt_type': 'claim',
                    'role_id': None
                }
            ])
        elif scene_type == 'confrontation':
            scriptlets.extend([
                {
                    'prompt_text': f'Present evidence that supports your position on {topic}',
                    'prompt_type': 'evidence',
                    'role_id': None
                },
                {
                    'prompt_text': f'Challenge a claim made by another participant with a counterargument',
                    'prompt_type': 'counterargument',
                    'role_id': None
                }
            ])
        elif scene_type == 'argumentation':
            scriptlets.extend([
                {
                    'prompt_text': f'Develop your argument further with additional evidence related to {topic}',
                    'prompt_type': 'evidence',
                    'role_id': None
                },
                {
                    'prompt_text': f'Respond to a counterargument by refining your position',
                    'prompt_type': 'claim',
                    'role_id': None
                }
            ])
        elif scene_type == 'conclusion':
            scriptlets.extend([
                {
                    'prompt_text': f'Synthesize the key points discussed about {topic}',
                    'prompt_type': 'synthesis',
                    'role_id': None
                },
                {
                    'prompt_text': f'Reflect on how the discussion addressed the learning objectives',
                    'prompt_type': 'synthesis',
                    'role_id': None
                }
            ])
        
        return scriptlets
