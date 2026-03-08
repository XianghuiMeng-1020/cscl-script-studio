"""Decision summary service for computing teacher decision metrics"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db import db
from app.models import CSCLTeacherDecision, CSCLScriptRevision


class DecisionSummaryService:
    """Service for computing decision summary metrics"""
    
    @staticmethod
    def compute_summary(script_id: str, 
                       spec_hash: Optional[str] = None,
                       config_fingerprint: Optional[str] = None,
                       provider: Optional[str] = None,
                       model: Optional[str] = None,
                       pipeline_run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute decision summary metrics
        
        Args:
            script_id: Script ID
            spec_hash: Optional spec hash for reproducibility
            config_fingerprint: Optional config fingerprint
            provider: Optional LLM provider name
            model: Optional model name
            pipeline_run_id: Optional pipeline run ID
        
        Returns:
            Summary dictionary with metrics
        """
        decisions = CSCLTeacherDecision.query.filter_by(script_id=script_id).all()
        
        if not decisions:
            return {
            'total_decisions': 0,
            'accept_rate': 0.0,
            'reject_rate': 0.0,
            'edit_rate': 0.0,
            'stage_adoption_rate': {},
            'avg_time_to_finalize': None,
            'evidence_linked_edit_rate': 0.0,
            'top_modified_target_types': [],
            'decision_count_by_stage': {},
            'decision_count_by_target_type': {},
            'reproducibility': {
                'spec_hash': spec_hash,
                'config_fingerprint': config_fingerprint,
                'provider': provider,
                'model': model,
                'pipeline_run_id': pipeline_run_id
            }
        }
        
        total = len(decisions)
        
        # Decision type rates
        accept_count = sum(1 for d in decisions if d.decision_type == 'accept')
        reject_count = sum(1 for d in decisions if d.decision_type == 'reject')
        edit_count = sum(1 for d in decisions if d.decision_type == 'edit')
        
        accept_rate = accept_count / total if total > 0 else 0.0
        reject_rate = reject_count / total if total > 0 else 0.0
        edit_rate = edit_count / total if total > 0 else 0.0
        
        # Stage adoption rate
        stage_counts = {}
        for stage in ['planner', 'material', 'critic', 'refiner', 'manual']:
            stage_decisions = [d for d in decisions if d.source_stage == stage]
            if stage_decisions:
                stage_accept = sum(1 for d in stage_decisions if d.decision_type == 'accept')
                stage_adoption = stage_accept / len(stage_decisions) if len(stage_decisions) > 0 else 0.0
                stage_counts[stage] = {
                    'adoption_rate': stage_adoption,
                    'total_decisions': len(stage_decisions),
                    'accept_count': stage_accept
                }
        
        # Average time to finalize
        finalize_decisions = [d for d in decisions if d.decision_type == 'finalize_note']
        avg_time_to_finalize = None
        if finalize_decisions:
            # Get first decision and last finalize
            first_decision = min(decisions, key=lambda d: d.created_at)
            last_finalize = max(finalize_decisions, key=lambda d: d.created_at)
            time_diff = (last_finalize.created_at - first_decision.created_at).total_seconds() / 60  # minutes
            avg_time_to_finalize = time_diff
        
        # Evidence linked edit rate
        edits_with_evidence = 0
        total_edits = 0
        for d in decisions:
            if d.decision_type == 'edit':
                total_edits += 1
                # Check if after_json contains evidence_refs
                if d.after_json and isinstance(d.after_json, dict):
                    if 'evidence_refs' in d.after_json or 'evidence_details' in d.after_json:
                        edits_with_evidence += 1
        
        evidence_linked_edit_rate = edits_with_evidence / total_edits if total_edits > 0 else 0.0
        
        # Top modified target types
        target_type_counts = {}
        for d in decisions:
            target_type_counts[d.target_type] = target_type_counts.get(d.target_type, 0) + 1
        
        top_modified = sorted(target_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_modified_target_types = [{'target_type': t, 'count': c} for t, c in top_modified]
        
        # Decision count by stage
        decision_count_by_stage = {}
        for stage in ['planner', 'material', 'critic', 'refiner', 'manual']:
            count = sum(1 for d in decisions if d.source_stage == stage)
            if count > 0:
                decision_count_by_stage[stage] = count
        
        # Decision count by target_type
        decision_count_by_target_type = {}
        for target_type in ['scene', 'role', 'scriptlet', 'material', 'evidence', 'pipeline_output']:
            count = sum(1 for d in decisions if d.target_type == target_type)
            if count > 0:
                decision_count_by_target_type[target_type] = count
        
        return {
            'total_decisions': total,
            'accept_rate': accept_rate,
            'reject_rate': reject_rate,
            'edit_rate': edit_rate,
            'stage_adoption_rate': stage_counts,
            'avg_time_to_finalize': avg_time_to_finalize,
            'evidence_linked_edit_rate': evidence_linked_edit_rate,
            'top_modified_target_types': top_modified_target_types,
            'decision_count_by_stage': decision_count_by_stage,
            'decision_count_by_target_type': decision_count_by_target_type,
            'reproducibility': {
                'spec_hash': spec_hash,
                'config_fingerprint': config_fingerprint,
                'provider': provider,
                'model': model,
                'pipeline_run_id': pipeline_run_id
            }
        }
    
    @staticmethod
    def get_timeline(script_id: str, 
                    decision_type: Optional[str] = None,
                    target_type: Optional[str] = None,
                    source_stage: Optional[str] = None,
                    actor_id: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get decision timeline
        
        Args:
            script_id: Script ID
            decision_type: Filter by decision type
            target_type: Filter by target type
            source_stage: Filter by source stage
            actor_id: Filter by actor ID
            start_time: Filter by start time
            end_time: Filter by end time
        
        Returns:
            List of decision dictionaries, sorted by created_at
        """
        query = CSCLTeacherDecision.query.filter_by(script_id=script_id)
        
        if decision_type:
            query = query.filter_by(decision_type=decision_type)
        if target_type:
            query = query.filter_by(target_type=target_type)
        if source_stage:
            query = query.filter_by(source_stage=source_stage)
        if actor_id:
            query = query.filter_by(actor_id=actor_id)
        if start_time:
            query = query.filter(CSCLTeacherDecision.created_at >= start_time)
        if end_time:
            query = query.filter(CSCLTeacherDecision.created_at <= end_time)
        
        decisions = query.order_by(CSCLTeacherDecision.created_at).all()
        
        return [d.to_dict() for d in decisions]
