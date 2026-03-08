"""Task type configuration: single source of truth for v1 argumentation-oriented taxonomy.
Purpose: stable script structure (play-scene-role-scriptlet) and generation quality.
Extensible via config/task_types.json without changing core logic.
"""
import json
import os
from typing import Dict, List, Any

_CONFIG_CACHE: Dict[str, Any] = {}
_DEFAULT_IDS = ['structured_debate', 'evidence_comparison', 'perspective_synthesis', 'claim_counterclaim_roleplay']


def _config_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'config', 'task_types.json')


def get_task_types_config() -> Dict[str, Any]:
    """Load task types from config/task_types.json; return dict with description and task_types list."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE:
        return _CONFIG_CACHE
    path = _config_path()
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _CONFIG_CACHE = json.load(f)
                return _CONFIG_CACHE
        except Exception:
            pass
    _CONFIG_CACHE = {
        'description': 'v1 collaborative argumentation task types for CSCL script generation.',
        'task_types': [
            {'id': 'structured_debate', 'display_name': 'Structured Debate', 'description': 'Position-based argumentation with evidence and rebuttals.', 'pedagogical_goal': 'Evidence-based argumentation and critical response.', 'expected_outputs': ['argument map', 'position statement'], 'minimum_role_pattern': 'proponent, opponent, moderator', 'compatible_modalities': ['sync', 'async']},
            {'id': 'evidence_comparison', 'display_name': 'Evidence Comparison', 'description': 'Compare and evaluate evidence; reach justified conclusion.', 'pedagogical_goal': 'Compare evidence quality and synthesize.', 'expected_outputs': ['comparison matrix', 'synthesis statement'], 'minimum_role_pattern': 'analyst, synthesizer, critic', 'compatible_modalities': ['sync', 'async']},
            {'id': 'perspective_synthesis', 'display_name': 'Perspective Synthesis', 'description': 'Integrate perspectives into shared artifact.', 'pedagogical_goal': 'Synthesize diverse perspectives.', 'expected_outputs': ['synthesis document', 'joint reflection'], 'minimum_role_pattern': 'contributor, synthesizer, reviewer', 'compatible_modalities': ['sync', 'async']},
            {'id': 'claim_counterclaim_roleplay', 'display_name': 'Claim–Counterclaim Role Play', 'description': 'Roles for claims and counterclaims; negotiate positions.', 'pedagogical_goal': 'Claim–counterclaim reasoning.', 'expected_outputs': ['role summary', 'position document'], 'minimum_role_pattern': 'claimant, counterclaimant, facilitator', 'compatible_modalities': ['sync', 'async']}
        ]
    }
    return _CONFIG_CACHE


def get_valid_task_type_ids() -> List[str]:
    """Return list of valid task_type ids (for validation). Uses config if present."""
    cfg = get_task_types_config()
    types = cfg.get('task_types') or []
    if types:
        return [t.get('id') for t in types if t.get('id')]
    return _DEFAULT_IDS


def get_task_types_for_api() -> Dict[str, Any]:
    """Return full config for API (description + task_types)."""
    return get_task_types_config()
