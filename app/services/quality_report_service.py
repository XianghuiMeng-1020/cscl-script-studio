"""Quality Report Service for CSCL Scripts"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db import db
from app.models import (
    CSCLScript, CSCLScene, CSCLRole, CSCLScriptlet,
    CSCLEvidenceBinding, CSCLTeacherDecision, CSCLPipelineRun, CSCLScriptRevision
)
from app.services.decision_summary_service import DecisionSummaryService
from app.services.cscl_pipeline_service import compute_spec_hash, compute_config_fingerprint


class QualityReportService:
    """Service for generating comprehensive quality reports for CSCL scripts"""
    
    REPORT_VERSION = 'c1-5.v1'
    
    @staticmethod
    def generate_report(script_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive quality report for a script
        
        Args:
            script_id: Script ID
        
        Returns:
            Quality report dictionary with fixed structure
        """
        script = CSCLScript.query.get(script_id)
        if not script:
            raise ValueError(f"Script {script_id} not found")
        
        # Load script structure
        scenes = CSCLScene.query.filter_by(script_id=script_id).order_by(CSCLScene.order_index).all()
        roles = CSCLRole.query.filter_by(script_id=script_id).all()
        scriptlets = []
        for scene in scenes:
            scene_scriptlets = CSCLScriptlet.query.filter_by(scene_id=scene.id).all()
            scriptlets.extend(scene_scriptlets)
        
        # Get pipeline run info for reproducibility
        latest_run = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
            CSCLPipelineRun.created_at.desc()
        ).first()
        
        spec_hash = None
        config_fingerprint = None
        if latest_run:
            spec_hash = latest_run.spec_hash
            config_fingerprint = latest_run.config_fingerprint
        
        # Collect data provenance
        pipeline_run_ids = [r.run_id for r in CSCLPipelineRun.query.filter_by(script_id=script_id).all()]
        revision_ids = [r.id for r in CSCLScriptRevision.query.filter_by(script_id=script_id).all()]
        decision_ids = [d.id for d in CSCLTeacherDecision.query.filter_by(script_id=script_id).all()]
        evidence_binding_ids = [b.id for b in CSCLEvidenceBinding.query.filter_by(script_id=script_id).all()]
        
        # Compute dimensions
        dimensions = QualityReportService._compute_dimensions(script, scenes, roles, scriptlets)
        
        # Compute overall summary
        summary = QualityReportService._compute_summary(dimensions, script, scenes, scriptlets)
        
        # Generate warnings
        warnings = QualityReportService._generate_warnings(dimensions, summary, script, scenes, scriptlets)
        
        return {
            'script_id': script_id,
            'report_version': QualityReportService.REPORT_VERSION,
            'computed_at': datetime.now().isoformat(),
            'spec_hash': spec_hash,
            'config_fingerprint': config_fingerprint,
            'summary': summary,
            'dimensions': dimensions,
            'warnings': warnings,
            'data_provenance': {
                'pipeline_run_ids': pipeline_run_ids,
                'revision_ids': revision_ids,
                'decision_ids': decision_ids,
                'evidence_binding_ids': evidence_binding_ids
            }
        }
    
    @staticmethod
    def _compute_dimensions(script: CSCLScript, scenes: List, roles: List, scriptlets: List) -> Dict[str, Any]:
        """Compute quality dimensions with scores, status, and evidence"""
        # Coverage
        learning_objectives = script.learning_objectives or []
        learning_objective_coverage = QualityReportService._compute_objective_coverage(
            scriptlets, learning_objectives
        )
        rubric_coverage_score = 0.8  # Placeholder - would check against rubric if available
        
        coverage_score = round((learning_objective_coverage * 0.7 + rubric_coverage_score * 0.3) * 100, 2)
        coverage_status = 'good' if coverage_score >= 70 else 'needs_attention' if coverage_score >= 50 else 'insufficient_data'
        
        coverage = {
            'score': coverage_score,
            'status': coverage_status,
            'evidence': {
                'learning_objective_coverage': round(learning_objective_coverage * 100, 2),
                'rubric_coverage': round(rubric_coverage_score * 100, 2),
                'objectives_count': len(learning_objectives),
                'scriptlets_count': len(scriptlets)
            }
        }
        
        # Pedagogical alignment
        task_type_alignment = QualityReportService._compute_task_type_alignment(
            script.task_type, scriptlets
        )
        duration_feasibility = QualityReportService._compute_duration_feasibility(
            script.duration_minutes, len(scenes), len(scriptlets)
        )
        role_balance = QualityReportService._compute_role_balance(roles, scriptlets)
        
        pedagogical_score = round((task_type_alignment * 0.4 + duration_feasibility * 0.3 + role_balance * 0.3) * 100, 2)
        pedagogical_status = 'good' if pedagogical_score >= 70 else 'needs_attention' if pedagogical_score >= 50 else 'insufficient_data'
        
        pedagogical_alignment = {
            'score': pedagogical_score,
            'status': pedagogical_status,
            'evidence': {
                'task_type_alignment': round(task_type_alignment * 100, 2),
                'duration_feasibility': round(duration_feasibility * 100, 2),
                'role_balance': round(role_balance * 100, 2),
                'task_type': script.task_type,
                'duration_minutes': script.duration_minutes,
                'scene_count': len(scenes),
                'role_count': len(roles)
            }
        }
        
        # Argumentation support
        argumentation_data = QualityReportService._compute_argumentation_support(scriptlets)
        has_all_types = argumentation_data['claim_presence'] and argumentation_data['evidence_presence']
        argumentation_score = round((1.0 if has_all_types else 0.5) * 100, 2)
        argumentation_status = 'good' if argumentation_score >= 70 else 'needs_attention'
        
        argumentation_support = {
            'score': argumentation_score,
            'status': argumentation_status,
            'evidence': argumentation_data
        }
        
        # Grounding
        evidence_bindings = CSCLEvidenceBinding.query.filter_by(script_id=script.id).all()
        scriptlet_ids_with_evidence = set(b.scriptlet_id for b in evidence_bindings if b.scriptlet_id)
        evidence_coverage = len(scriptlet_ids_with_evidence) / max(len(scriptlets), 1) if scriptlets else 0.0
        ungrounded_scriptlet_count = len(scriptlets) - len(scriptlet_ids_with_evidence)
        
        grounding_score = round(evidence_coverage * 100, 2)
        grounding_status = 'good' if grounding_score >= 70 else 'needs_attention' if grounding_score >= 30 else 'insufficient_data'
        
        grounding = {
            'score': grounding_score,
            'status': grounding_status,
            'evidence': {
                'evidence_coverage': round(evidence_coverage * 100, 2),
                'ungrounded_scriptlet_count': ungrounded_scriptlet_count,
                'total_scriptlets': len(scriptlets),
                'evidence_bindings_count': len(evidence_bindings)
            }
        }
        
        # Safety checks
        safety_data = QualityReportService._compute_safety_checks(scriptlets)
        safety_score = round((1.0 - min(len(safety_data['sensitive_content_flags']) / max(len(scriptlets), 1), 1.0)) * 100, 2)
        safety_status = 'good' if not safety_data['has_sensitive_content'] else 'needs_attention'
        
        safety_checks = {
            'score': safety_score,
            'status': safety_status,
            'evidence': safety_data,
            'has_sensitive_content': safety_data.get('has_sensitive_content', False),
            'has_missing_citations': safety_data.get('has_missing_citations', False)
        }
        
        # Teacher in loop (from C1-4)
        decision_summary = DecisionSummaryService.compute_summary(script.id)
        accept_rate = decision_summary.get('accept_rate', 0.0)
        edit_rate = decision_summary.get('edit_rate', 0.0)
        reject_rate = decision_summary.get('reject_rate', 0.0)
        total_decisions = decision_summary.get('total_decisions', 0)
        
        # Score based on acceptance rate and engagement
        teacher_score = round((accept_rate * 0.6 + (1 - reject_rate) * 0.4) * 100, 2) if total_decisions > 0 else 50.0
        teacher_status = 'good' if teacher_score >= 70 else 'needs_attention' if total_decisions > 0 else 'insufficient_data'
        
        teacher_in_loop = {
            'score': teacher_score,
            'status': teacher_status,
            'evidence': {
                'accept_rate': round(accept_rate * 100, 2),
                'edit_rate': round(edit_rate * 100, 2),
                'reject_rate': round(reject_rate * 100, 2),
                'total_decisions': total_decisions,
                'stage_adoption_rate': decision_summary.get('stage_adoption_rate', {})
            }
        }
        
        return {
            'coverage': coverage,
            'pedagogical_alignment': pedagogical_alignment,
            'argumentation_support': argumentation_support,
            'grounding': grounding,
            'safety_checks': safety_checks,
            'teacher_in_loop': teacher_in_loop
        }
    
    @staticmethod
    def _compute_summary(dimensions: Dict[str, Any], script: CSCLScript, scenes: List, scriptlets: List) -> Dict[str, Any]:
        """Compute overall summary"""
        scores = [d['score'] for d in dimensions.values() if isinstance(d, dict) and 'score' in d]
        
        if not scores:
            return {
                'overall_score': 0,
                'status': 'insufficient_data'
            }
        
        overall_score = round(sum(scores) / len(scores), 2)
        
        if overall_score >= 70:
            status = 'good'
        elif overall_score >= 50:
            status = 'needs_attention'
        else:
            status = 'insufficient_data'
        
        return {
            'overall_score': overall_score,
            'status': status
        }
    
    @staticmethod
    def _generate_warnings(dimensions: Dict[str, Any], summary: Dict[str, Any], 
                          script: CSCLScript, scenes: List, scriptlets: List) -> List[str]:
        """Generate warnings based on dimensions and summary"""
        warnings = []
        
        if summary['status'] == 'insufficient_data':
            warnings.append('Insufficient data for comprehensive quality assessment')
        
        if dimensions['grounding']['status'] == 'insufficient_data':
            warnings.append('Low evidence coverage - consider uploading course documents')
        
        if dimensions['coverage']['status'] == 'needs_attention':
            warnings.append('Learning objective coverage needs improvement')
        
        if dimensions.get('safety_checks', {}).get('has_sensitive_content', False):
            warnings.append('Potential sensitive content detected - review recommended')
        
        if dimensions['teacher_in_loop']['status'] == 'insufficient_data':
            warnings.append('No teacher decisions recorded - quality assessment limited')
        
        return warnings
    
    @staticmethod
    def _compute_objective_coverage(scriptlets: List, objectives: List[str]) -> float:
        """Compute how well scriptlets cover learning objectives"""
        if not objectives:
            return 1.0  # No objectives to cover
        
        if not scriptlets:
            return 0.0  # No scriptlets to cover objectives
        
        # Simple keyword matching (can be enhanced)
        objective_keywords = set()
        for obj in objectives:
            if obj:
                objective_keywords.update(obj.lower().split())
        
        if not objective_keywords:
            return 1.0  # No meaningful keywords
        
        covered_keywords = set()
        for scriptlet in scriptlets:
            if scriptlet.prompt_text:
                prompt_text = scriptlet.prompt_text.lower()
                for keyword in objective_keywords:
                    if keyword in prompt_text:
                        covered_keywords.add(keyword)
        
        return len(covered_keywords) / max(len(objective_keywords), 1)
    
    @staticmethod
    def _compute_task_type_alignment(task_type: str, scriptlets: List) -> float:
        """Compute alignment with task type"""
        # Check for task-specific prompt types
        task_requirements = {
            'debate': ['claim', 'evidence', 'counterargument'],
            'structured_debate': ['claim', 'evidence', 'counterargument'],
            'evidence_comparison': ['evidence', 'synthesis'],
            'perspective_synthesis': ['synthesis', 'evidence'],
            'claim_counterclaim_roleplay': ['claim', 'counterargument'],
            'collaborative_writing': ['synthesis', 'evidence'],
            'peer_review': ['claim', 'evidence']
        }
        
        required_types = task_requirements.get(task_type, [])
        if not required_types:
            return 0.8  # Default score
        
        scriptlet_types = [s.prompt_type for s in scriptlets]
        present_types = [t for t in required_types if t in scriptlet_types]
        
        return len(present_types) / max(len(required_types), 1)
    
    @staticmethod
    def _compute_duration_feasibility(duration_minutes: int, scene_count: int, scriptlet_count: int) -> float:
        """Compute if duration is feasible for script complexity"""
        # Rough estimate: 5 minutes per scene, 1 minute per scriptlet
        estimated_minutes = scene_count * 5 + scriptlet_count * 1
        ratio = duration_minutes / max(estimated_minutes, 1)
        
        # Score: 1.0 if ratio is between 0.8 and 1.2, decreasing outside
        if 0.8 <= ratio <= 1.2:
            return 1.0
        elif ratio < 0.8:
            return ratio / 0.8  # Too short
        else:
            return 1.2 / ratio  # Too long
    
    @staticmethod
    def _compute_role_balance(roles: List, scriptlets: List) -> float:
        """Compute balance of scriptlets across roles"""
        if not roles:
            return 0.0
        
        role_scriptlet_counts = {}
        for scriptlet in scriptlets:
            role_id = scriptlet.role_id
            role_scriptlet_counts[role_id] = role_scriptlet_counts.get(role_id, 0) + 1
        
        if not role_scriptlet_counts:
            return 0.0
        
        counts = list(role_scriptlet_counts.values())
        avg_count = sum(counts) / len(counts)
        variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
        std_dev = variance ** 0.5
        
        # Score decreases with variance
        return max(0.0, 1.0 - (std_dev / max(avg_count, 1)))
    
    @staticmethod
    def _compute_argumentation_support(scriptlets: List) -> Dict[str, Any]:
        """Compute argumentation support metrics"""
        if not scriptlets:
            return {
                'claim_presence': False,
                'evidence_presence': False,
                'rebuttal_presence': False,
                'claim_count': 0,
                'evidence_count': 0,
                'rebuttal_count': 0
            }
        
        claim_count = sum(1 for s in scriptlets if s.prompt_type == 'claim')
        evidence_count = sum(1 for s in scriptlets if s.prompt_type == 'evidence')
        rebuttal_count = sum(1 for s in scriptlets if s.prompt_type == 'counterargument')
        
        return {
            'claim_presence': claim_count > 0,
            'evidence_presence': evidence_count > 0,
            'rebuttal_presence': rebuttal_count > 0,
            'claim_count': claim_count,
            'evidence_count': evidence_count,
            'rebuttal_count': rebuttal_count
        }
    
    @staticmethod
    def _compute_safety_checks(scriptlets: List) -> Dict[str, Any]:
        """Compute safety check flags"""
        if not scriptlets:
            return {
                'sensitive_content_flags': [],
                'missing_citation_warnings': [],
                'has_sensitive_content': False,
                'has_missing_citations': False
            }
        
        # Simple keyword-based sensitive content detection
        sensitive_keywords = ['violence', 'hate', 'discrimination']  # Simplified
        sensitive_content_flags = []
        
        for scriptlet in scriptlets:
            if scriptlet.prompt_text:
                prompt_lower = scriptlet.prompt_text.lower()
                for keyword in sensitive_keywords:
                    if keyword in prompt_lower:
                        sensitive_content_flags.append({
                            'scriptlet_id': scriptlet.id,
                            'keyword': keyword,
                            'severity': 'low'  # Placeholder
                        })
        
        # Missing citation warnings (scriptlets without evidence_refs)
        missing_citation_warnings = []
        scriptlet_ids = [s.id for s in scriptlets]
        if scriptlet_ids:
            evidence_bindings = CSCLEvidenceBinding.query.filter(
                CSCLEvidenceBinding.scriptlet_id.in_(scriptlet_ids)
            ).all()
            scriptlets_with_evidence = set(b.scriptlet_id for b in evidence_bindings if b.scriptlet_id)
            
            for scriptlet in scriptlets:
                if scriptlet.id not in scriptlets_with_evidence:
                    missing_citation_warnings.append({
                        'scriptlet_id': scriptlet.id,
                        'prompt_type': scriptlet.prompt_type
                    })
        
        return {
            'sensitive_content_flags': sensitive_content_flags,
            'missing_citation_warnings': missing_citation_warnings,
            'has_sensitive_content': len(sensitive_content_flags) > 0,
            'has_missing_citations': len(missing_citation_warnings) > 0
        }
    
