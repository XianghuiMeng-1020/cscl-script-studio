"""Helper functions for automatic decision tracking"""
from typing import Dict, Any, Optional
from app.db import db
from app.models import CSCLTeacherDecision, CSCLScriptRevision


def create_decision_auto(script_id: str, actor_id: str, decision_type: str, target_type: str,
                         target_id: Optional[str] = None, before_json: Optional[Dict] = None,
                         after_json: Optional[Dict] = None, source_stage: Optional[str] = None,
                         revision_id: Optional[str] = None, rationale_text: Optional[str] = None,
                         confidence: Optional[int] = None) -> CSCLTeacherDecision:
    """
    Automatically create a decision record
    
    Args:
        script_id: Script ID
        actor_id: Actor user ID
        decision_type: Type of decision
        target_type: Type of target
        target_id: Optional target ID
        before_json: Optional before state
        after_json: Optional after state
        source_stage: Optional source stage
        revision_id: Optional revision ID
        rationale_text: Optional rationale
        confidence: Optional confidence (1-5)
    
    Returns:
        Created decision object
    """
    decision = CSCLTeacherDecision(
        script_id=script_id,
        revision_id=revision_id,
        actor_id=actor_id,
        decision_type=decision_type,
        target_type=target_type,
        target_id=target_id,
        before_json=before_json,
        after_json=after_json,
        rationale_text=rationale_text,
        source_stage=source_stage,
        confidence=confidence
    )
    
    db.session.add(decision)
    db.session.flush()
    
    return decision


def detect_edits_and_create_decisions(script_id: str, actor_id: str, before_state: Dict[str, Any],
                                     after_state: Dict[str, Any], revision_id: Optional[str] = None,
                                     source_stage: Optional[str] = None) -> list:
    """
    Detect edits between before and after states and create decision records
    
    Args:
        script_id: Script ID
        actor_id: Actor user ID
        before_state: Before state dictionary
        after_state: After state dictionary
        revision_id: Optional revision ID
        source_stage: Optional source stage
    
    Returns:
        List of created decision objects
    """
    decisions = []
    
    # Compare scenes
    before_scenes = {s.get('id'): s for s in before_state.get('scenes', [])}
    after_scenes = {s.get('id'): s for s in after_state.get('scenes', [])}
    
    # Detect scene edits
    for scene_id, after_scene in after_scenes.items():
        if scene_id in before_scenes:
            before_scene = before_scenes[scene_id]
            if before_scene != after_scene:
                decision = create_decision_auto(
                    script_id=script_id,
                    actor_id=actor_id,
                    decision_type='edit',
                    target_type='scene',
                    target_id=scene_id,
                    before_json=before_scene,
                    after_json=after_scene,
                    revision_id=revision_id,
                    source_stage=source_stage
                )
                decisions.append(decision)
        else:
            # New scene
            decision = create_decision_auto(
                script_id=script_id,
                actor_id=actor_id,
                decision_type='add',
                target_type='scene',
                target_id=scene_id,
                after_json=after_scene,
                revision_id=revision_id,
                source_stage=source_stage
            )
            decisions.append(decision)
    
    # Detect deleted scenes
    for scene_id in before_scenes:
        if scene_id not in after_scenes:
            decision = create_decision_auto(
                script_id=script_id,
                actor_id=actor_id,
                decision_type='delete',
                target_type='scene',
                target_id=scene_id,
                before_json=before_scenes[scene_id],
                revision_id=revision_id,
                source_stage=source_stage
            )
            decisions.append(decision)
    
    # Compare scriptlets (nested in scenes)
    for scene_id, after_scene in after_scenes.items():
        before_scene = before_scenes.get(scene_id, {})
        before_scriptlets = {s.get('id'): s for s in before_scene.get('scriptlets', [])}
        after_scriptlets = {s.get('id'): s for s in after_scene.get('scriptlets', [])}
        
        # Detect scriptlet edits
        for scriptlet_id, after_scriptlet in after_scriptlets.items():
            if scriptlet_id in before_scriptlets:
                before_scriptlet = before_scriptlets[scriptlet_id]
                if before_scriptlet != after_scriptlet:
                    decision = create_decision_auto(
                        script_id=script_id,
                        actor_id=actor_id,
                        decision_type='edit',
                        target_type='scriptlet',
                        target_id=scriptlet_id,
                        before_json=before_scriptlet,
                        after_json=after_scriptlet,
                        revision_id=revision_id,
                        source_stage=source_stage
                    )
                    decisions.append(decision)
            else:
                # New scriptlet
                decision = create_decision_auto(
                    script_id=script_id,
                    actor_id=actor_id,
                    decision_type='add',
                    target_type='scriptlet',
                    target_id=scriptlet_id,
                    after_json=after_scriptlet,
                    revision_id=revision_id,
                    source_stage=source_stage
                )
                decisions.append(decision)
        
        # Detect deleted scriptlets
        for scriptlet_id in before_scriptlets:
            if scriptlet_id not in after_scriptlets:
                decision = create_decision_auto(
                    script_id=script_id,
                    actor_id=actor_id,
                    decision_type='delete',
                    target_type='scriptlet',
                    target_id=scriptlet_id,
                    before_json=before_scriptlets[scriptlet_id],
                    revision_id=revision_id,
                    source_stage=source_stage
                )
                decisions.append(decision)
    
    return decisions
