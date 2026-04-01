"""CSCL Pipeline Service - orchestrates multi-stage generation"""
from flask import current_app
from typing import Dict, Any, Optional, List
import hashlib
import json
import uuid
import os
from datetime import datetime, timezone
from app.db import db
from app.models import (
    CSCLPipelineRun,
    CSCLPipelineStageRun,
    CSCLEvidenceBinding,
    CSCLScript,
    CSCLScene,
    CSCLScriptlet,
)
from app.services.pipeline.planner import PlannerStage
from app.services.pipeline.material_generator import MaterialGeneratorStage
from app.services.pipeline.critic import CriticStage
from app.services.pipeline.refiner import RefinerStage
from app.services.cscl_llm_provider import get_cscl_llm_provider, select_runnable_provider, is_provider_runnable
from app.services.cscl_retriever import CSCLRetriever
import logging

logger = logging.getLogger(__name__)

PIPELINE_VERSION = '1.0.0'


def compute_spec_hash(spec: Dict[str, Any]) -> str:
    """Compute hash of normalized spec for reproducibility"""
    spec_str = json.dumps(spec, sort_keys=True)
    return hashlib.sha256(spec_str.encode()).hexdigest()


def compute_config_fingerprint(options: Dict[str, Any], provider: str, model: str) -> str:
    """Compute fingerprint of generation config for reproducibility"""
    config = {
        'provider': provider,
        'model': model,
        'temperature': options.get('temperature', 0.7),
        'max_tokens': options.get('max_tokens', 1000),
        'seed': options.get('seed'),
        'pipeline_version': PIPELINE_VERSION
    }
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()


def compute_quality_report(refiner_output: Dict[str, Any], spec: Dict[str, Any], 
                          evidence_binding_ratio: float = 0.0) -> Dict[str, Any]:
    """Compute quality report for pipeline result"""
    scenes = refiner_output.get('scenes', [])
    roles = refiner_output.get('roles', [])
    
    # Coverage
    required_fields = ['scenes', 'roles']
    required_fields_coverage = sum(1 for field in required_fields if refiner_output.get(field))
    scene_completeness = len(scenes) / max(4, 1)  # Normalize to 4 scenes
    role_completeness = len(roles) / max(3, 1)  # Normalize to 3 roles
    
    # Pedagogical alignment
    task_type = spec['task_requirements']['task_type']
    objectives = spec['learning_objectives']
    objective_alignment_score = 0.8  # Placeholder - would analyze script against objectives
    task_fit_score = 0.8  # Placeholder - would analyze script fit to task_type
    
    # Argumentation support
    scriptlets = []
    for scene in scenes:
        scriptlets.extend(scene.get('scriptlets', []))
    
    claim_count = sum(1 for s in scriptlets if s.get('prompt_type') == 'claim')
    evidence_count = sum(1 for s in scriptlets if s.get('prompt_type') == 'evidence')
    counterargument_count = sum(1 for s in scriptlets if s.get('prompt_type') == 'counterargument')
    
    claim_evidence_counterargument_presence = {
        'has_claims': claim_count > 0,
        'has_evidence': evidence_count > 0,
        'has_counterarguments': counterargument_count > 0,
        'claim_count': claim_count,
        'evidence_count': evidence_count,
        'counterargument_count': counterargument_count
    }
    
    # Grounding (C1-3: RAG integration)
    # evidence_binding_ratio is passed as parameter
    
    # Safety checks
    hallucination_risk_flag = False  # Placeholder
    unsupported_claim_count = 0  # Placeholder
    
    return {
        'coverage': {
            'required_fields_coverage': required_fields_coverage / len(required_fields),
            'scene_completeness': min(scene_completeness, 1.0),
            'role_completeness': min(role_completeness, 1.0)
        },
        'pedagogical_alignment': {
            'objective_alignment_score': objective_alignment_score,
            'task_fit_score': task_fit_score
        },
        'argumentation_support': {
            'claim_evidence_counterargument_presence': claim_evidence_counterargument_presence
        },
        'grounding': {
            'evidence_binding_ratio': evidence_binding_ratio,
            'status': 'pending'  # Will be enhanced in C1-3
        },
        'safety_checks': {
            'hallucination_risk_flag': hallucination_risk_flag,
            'unsupported_claim_count': unsupported_claim_count
        }
    }


class CSCLPipelineService:
    """Service for orchestrating multi-stage CSCL script generation with optional web retrieval and image generation"""
    
    def __init__(self, enable_rag: bool = True, force_provider: Optional[str] = None, enable_web_retrieval: bool = False, enable_image_generation: bool = False):
        """
        Initialize pipeline service
        
        Args:
            enable_rag: Whether to enable RAG retrieval (default: True)
            force_provider: Optional provider name to force (for retry scenarios)
            enable_web_retrieval: Whether to enable web retrieval for external examples
            enable_image_generation: Whether to enable AI image generation for visuals
        """
        self.force_provider = force_provider
        self.provider = get_cscl_llm_provider(force_provider=force_provider)
        self.planner = PlannerStage(self.provider)
        self.material_generator = MaterialGeneratorStage(self.provider)
        self.critic = CriticStage(self.provider)
        self.refiner = RefinerStage(self.provider)
        self.retriever = CSCLRetriever(k=5) if enable_rag else None
        
        # B1/B2: AI Enhancement services
        self.enable_web_retrieval = enable_web_retrieval
        self.enable_image_generation = enable_image_generation
        
        if enable_web_retrieval:
            from app.services.web_retrieval_service import get_web_retrieval_service
            self.web_retrieval_service = get_web_retrieval_service()
        else:
            self.web_retrieval_service = None
            
        if enable_image_generation:
            from app.services.image_generation_service import get_image_generation_service
            self.image_generation_service = get_image_generation_service()
        else:
            self.image_generation_service = None
    
    def _retrieve_evidence(self, spec: Dict[str, Any], stage_name: str, script_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve evidence chunks for a stage
        
        Returns:
            List of retrieved chunks with metadata
        """
        if not self.retriever:
            return []
        
        # Get course_id from script (fallback to default-course for compatibility)
        script = db.session.get(CSCLScript, script_id)
        course_id = script.course_id if script else spec.get('course_context', {}).get('course_id')
        
        if not course_id:
            course_id = 'default-course'
        
        # Construct query
        query = self.retriever.construct_query(spec, stage_name)
        
        # Retrieve chunks
        chunks = self.retriever.retrieve(query, course_id, binding_type=stage_name)
        
        return chunks
    
    def _persist_material_output_to_script(
        self, script_id: str, material_output: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Persist scenes/scriptlets from material output to DB.
        Returns mapping: placeholder_id -> real_uuid
        """
        mapping: Dict[str, str] = {}
        scenes = material_output.get('scenes') or []
        if not scenes:
            return mapping

        # Delete existing evidence_bindings for this script, then scriptlets, then scenes
        CSCLEvidenceBinding.query.filter_by(script_id=script_id).delete(
            synchronize_session=False
        )
        existing_scenes = CSCLScene.query.filter_by(script_id=script_id).all()
        for scene in existing_scenes:
            CSCLScriptlet.query.filter_by(scene_id=scene.id).delete()
        CSCLScene.query.filter_by(script_id=script_id).delete()
        db.session.flush()

        for scene_idx, scene_data in enumerate(scenes):
            if not isinstance(scene_data, dict):
                continue
            placeholder_scene = f"scene_{scene_idx}"
            scene = CSCLScene(
                script_id=script_id,
                order_index=int(scene_data.get('order_index', scene_idx + 1)),
                scene_type=str(scene_data.get('scene_type', 'unknown')),
                purpose=scene_data.get('purpose'),
                transition_rule=scene_data.get('transition_rule'),
            )
            db.session.add(scene)
            db.session.flush()
            mapping[placeholder_scene] = scene.id

            for scriptlet_idx, sl_data in enumerate(scene_data.get('scriptlets') or []):
                if not isinstance(sl_data, dict):
                    continue
                placeholder_scriptlet = f"scriptlet_{scene_idx}_{scriptlet_idx}"
                scriptlet = CSCLScriptlet(
                    scene_id=scene.id,
                    role_id=None,  # role_id may be string like "Facilitator"; use None for FK
                    prompt_text=str(sl_data.get('prompt_text', '')),
                    prompt_type=str(sl_data.get('prompt_type', 'claim')),
                    resource_ref=sl_data.get('resource_ref'),
                )
                db.session.add(scriptlet)
                db.session.flush()
                mapping[placeholder_scriptlet] = scriptlet.id
        db.session.flush()
        return mapping

    def _bind_evidence(
        self,
        script_id: str,
        scene_id: Optional[str],
        scriptlet_id: Optional[str],
        chunk_id: str,
        relevance_score: float,
        binding_type: str,
        id_mapping: Optional[Dict[str, str]] = None,
    ):
        """Create evidence binding record. Uses id_mapping to replace placeholder IDs."""
        real_scene = (id_mapping or {}).get(scene_id) if scene_id else None
        real_scriptlet = (id_mapping or {}).get(scriptlet_id) if scriptlet_id else None
        if scene_id and not real_scene:
            logger.warning(
                "evidence_binding: scene_id %s not in mapping, skipping binding",
                scene_id,
            )
            return
        if scriptlet_id and not real_scriptlet:
            logger.warning(
                "evidence_binding: scriptlet_id %s not in mapping, skipping binding",
                scriptlet_id,
            )
            return
        binding = CSCLEvidenceBinding(
            script_id=script_id,
            scene_id=real_scene,
            scriptlet_id=real_scriptlet,
            chunk_id=chunk_id,
            relevance_score=relevance_score,
            binding_type=binding_type,
        )
        db.session.add(binding)
    
    def _add_evidence_refs_to_output(
        self,
        output: Dict[str, Any],
        evidence_chunks: List[Dict[str, Any]],
        binding_type: str,
        script_id: str,
        id_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Add evidence_refs to output structure and create bindings.
        id_mapping: optional placeholder -> real UUID; if provided, bindings use real IDs or skip with warning.
        """
        if not evidence_chunks:
            return
        
        chunk_ids = [c['chunk_id'] for c in evidence_chunks]
        scenes = output.get('scenes', [])
        for scene_idx, scene in enumerate(scenes):
            scene_id = scene.get('id') or f"scene_{scene_idx}"
            if 'evidence_refs' not in scene:
                scene['evidence_refs'] = []
            scene['evidence_refs'].extend(chunk_ids)

            scriptlets = scene.get('scriptlets', [])
            for scriptlet_idx, scriptlet in enumerate(scriptlets):
                scriptlet_id = scriptlet.get('id') or f"scriptlet_{scene_idx}_{scriptlet_idx}"
                if 'evidence_refs' not in scriptlet:
                    scriptlet['evidence_refs'] = []
                scriptlet['evidence_refs'].extend(chunk_ids)

                for chunk in evidence_chunks:
                    self._bind_evidence(
                        script_id=script_id,
                        scene_id=scene_id,
                        scriptlet_id=scriptlet_id,
                        chunk_id=chunk['chunk_id'],
                        relevance_score=chunk['relevance_score'],
                        binding_type=binding_type,
                        id_mapping=id_mapping,
                    )
    
    def run_pipeline(self, script_id: str, spec: Dict[str, Any], initiated_by: str,
                    options: Dict[str, Any] = None, run_id_override: str = None) -> Dict[str, Any]:
        """
        Run complete pipeline
        
        Args:
            script_id: Script ID
            spec: Normalized pedagogical specification
            initiated_by: User ID who initiated the run
            options: Generation options
            run_id_override: If given, use this run_id instead of generating one
        
        Returns:
            {
                'run_id': str,
                'status': str,
                'stages': [...],
                'final_output': {...},
                'quality_report': {...},
                'grounding_status': str,
                'error': str or None
            }
        """
        options = options or {}
        run_id = run_id_override or f"run_{uuid.uuid4().hex[:16]}"
        spec_hash = compute_spec_hash(spec)
        
        # Check grounding status
        script = db.session.get(CSCLScript, script_id)
        course_id = script.course_id if script else spec.get('course_context', {}).get('course_id')
        
        from app.models import CSCLCourseDocument
        has_docs = CSCLCourseDocument.query.filter_by(course_id=course_id).first() is not None if course_id else False
        grounding_status = 'no_course_docs' if not has_docs else 'grounded'
        
        # Create pipeline run record
        pipeline_run = CSCLPipelineRun(
            run_id=run_id,
            script_id=script_id,
            initiated_by=initiated_by,
            spec_hash=spec_hash,
            pipeline_version=PIPELINE_VERSION,
            status='running'
        )
        
        try:
            db.session.add(pipeline_run)
            db.session.flush()
            
            stages = []
            final_output = None
            error_message = None
            
            # S2.18: Fail-fast check - verify provider readiness before starting
            # Use select_runnable_provider as single point of selection
            provider_status = select_runnable_provider()
            if not provider_status['ready']:
                # Provider not ready - don't create run record, return immediately
                db.session.rollback()
                return {
                    'ok': False,
                    'http_status': 503,
                    'code': 'LLM_PROVIDER_NOT_READY',
                    'error': provider_status['reason'],
                    'details': {
                        'primary': provider_status['primary'],
                        'fallback': provider_status['fallback'],
                        'strategy': provider_status['strategy'],
                        'checks': provider_status['checks']
                    },
                    'stages': []
                }
            
            # Stage 1: Planner (with RAG retrieval and fallback retry)
            evidence_chunks_planner = self._retrieve_evidence(spec, 'planner', script_id) if self.retriever else []
            planner_options = (options or {}).copy()
            planner_options['run_id'] = run_id
            planner_result = self.planner.run(spec, planner_options)
            planner_result['retrieved_chunks_count'] = len(evidence_chunks_planner)
            planner_result['retrieved_chunk_ids'] = [c['chunk_id'] for c in evidence_chunks_planner]
            
            # S2.18: Error classification and fallback retry logic
            attempted_providers = set()
            if 'stage_attempts' in planner_result:
                attempted_providers.add(planner_result.get('provider', 'unknown'))
            else:
                attempted_providers.add(planner_result.get('provider', 'unknown'))
            
            # Check for provider-not-ready errors
            error_msg = (planner_result.get('error') or '').lower()
            provider_not_ready_patterns = [
                'not implemented', 'not fully implemented',
                'provider not runnable', 'api key missing', 'disabled',
                'not configured', 'not available'
            ]
            
            is_provider_error = any(pattern in error_msg for pattern in provider_not_ready_patterns)
            
            if planner_result['status'] != 'success' and is_provider_error:
                # Provider error - check if we can fallback
                fallback_name = provider_status['fallback']
                primary_name = provider_status['primary']
                strategy = provider_status['strategy']
                
                # Only retry if: fallback exists, different from primary, runnable, not already attempted
                can_fallback = (
                    strategy in ('primary_with_fallback', 'fallback_only') and
                    fallback_name != primary_name and
                    fallback_name not in attempted_providers and
                    provider_status['checks']['fallback']['runnable']
                )
                
                if can_fallback:
                    # Record primary attempt
                    stage_attempts = planner_result.get('stage_attempts', [])
                    if not stage_attempts:
                        stage_attempts = [{
                            'provider': planner_result.get('provider', primary_name),
                            'status': 'failed',
                            'error': planner_result.get('error'),
                            'latency_ms': planner_result.get('latency_ms', 0)
                        }]
                    
                    # Retry with fallback
                    from app.services.cscl_llm_provider import get_cscl_llm_provider
                    fallback_provider = get_cscl_llm_provider(force_provider=fallback_name)
                    fallback_planner = PlannerStage(fallback_provider)
                    
                    fallback_result = fallback_planner.run(spec, options)
                    fallback_result['retrieved_chunks_count'] = len(evidence_chunks_planner)
                    fallback_result['retrieved_chunk_ids'] = [c['chunk_id'] for c in evidence_chunks_planner]
                    
                    # Record fallback attempt
                    stage_attempts.append({
                        'provider': fallback_result.get('provider', fallback_name),
                        'status': fallback_result['status'],
                        'error': fallback_result.get('error'),
                        'latency_ms': fallback_result.get('latency_ms', 0)
                    })
                    
                    fallback_result['stage_attempts'] = stage_attempts
                    planner_result = fallback_result
                    
                    # Update provider in pipeline
                    self.provider = fallback_provider
                    self.planner = fallback_planner
                    self.material_generator = MaterialGeneratorStage(fallback_provider)
                    self.critic = CriticStage(fallback_provider)
                    self.refiner = RefinerStage(fallback_provider)
                else:
                    # Cannot fallback - return provider not ready error
                    db.session.rollback()
                    return {
                        'ok': False,
                        'http_status': 503,
                        'code': 'LLM_PROVIDER_NOT_READY',
                        'error': f"Provider error: {planner_result.get('error')}",
                        'details': {
                            'primary': primary_name,
                            'fallback': fallback_name,
                            'strategy': strategy,
                            'checks': provider_status['checks']
                        },
                        'stages': []
                    }
            
            stages.append(planner_result)
            self._save_stage_run(run_id, planner_result)
            
            if planner_result['status'] != 'success':
                pipeline_run.status = 'failed'
                pipeline_run.error_message = f"Planner failed: {planner_result.get('error')}"
                pipeline_run.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'run_id': run_id,
                    'status': 'failed',
                    'code': 'PIPELINE_FAILED',
                    'stages': stages,
                    'final_output': None,
                    'quality_report': None,
                    'grounding_status': grounding_status,
                    'error': planner_result.get('error')
                }
            
            # Add evidence refs to planner output
            if evidence_chunks_planner:
                self._add_evidence_refs_to_output(
                    planner_result['output_snapshot'],
                    evidence_chunks_planner,
                    'planner',
                    script_id
                )
            
            # B2: Web Retrieval Stage (optional, between Planner and Material Generator)
            web_retrieval_result = None
            if self.enable_web_retrieval and self.web_retrieval_service and self.web_retrieval_service.is_enabled():
                try:
                    web_retrieval_result = self.web_retrieval_service.retrieve_lesson_materials(
                        spec=spec,
                        retrieval_type="all"
                    )
                    if web_retrieval_result.get('success'):
                        # Add retrieved materials to material_options for the generator to use
                        material_options = (options or {}).copy()
                        material_options['run_id'] = run_id
                        material_options['web_retrieval_results'] = web_retrieval_result
                        material_options['web_retrieval_formatted'] = self.web_retrieval_service.format_for_prompt(web_retrieval_result)
                        logger.info(f"[Pipeline] Web retrieval completed for run {run_id}")
                    else:
                        logger.warning(f"[Pipeline] Web retrieval failed: {web_retrieval_result.get('error')}")
                except Exception as e:
                    logger.error(f"[Pipeline] Web retrieval error: {str(e)}")
            
            # Stage 2: Material Generator (with RAG retrieval)
            evidence_chunks_material = self._retrieve_evidence(spec, 'material_generator', script_id) if self.retriever else []
            material_options = (options or {}).copy()
            material_options['run_id'] = run_id
            
            # B2: Include web retrieval results if available
            if web_retrieval_result and web_retrieval_result.get('success'):
                material_options['web_retrieval_results'] = web_retrieval_result
                material_options['web_retrieval_formatted'] = self.web_retrieval_service.format_for_prompt(web_retrieval_result)
            
            material_result = self.material_generator.run(planner_result['output_snapshot'], spec, material_options)
            material_result['retrieved_chunks_count'] = len(evidence_chunks_material)
            material_result['retrieved_chunk_ids'] = [c['chunk_id'] for c in evidence_chunks_material]
            material_result['web_retrieval_used'] = web_retrieval_result is not None and web_retrieval_result.get('success', False)
            stages.append(material_result)
            self._save_stage_run(run_id, material_result)
            
            if material_result['status'] != 'success':
                pipeline_run.status = 'partial_failed'
                pipeline_run.error_message = f"Material generator failed: {material_result.get('error')}"
                pipeline_run.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'run_id': run_id,
                    'status': 'partial_failed',
                    'stages': stages,
                    'final_output': material_result.get('output_snapshot'),
                    'quality_report': None,
                    'grounding_status': grounding_status,
                    'error': material_result.get('error')
                }

            # Persist material output scenes/scriptlets so evidence_bindings can use real UUIDs
            id_mapping = self._persist_material_output_to_script(
                script_id, material_result['output_snapshot']
            )

            # Add evidence refs to material output (with mapping so bindings use real IDs)
            if evidence_chunks_material:
                self._add_evidence_refs_to_output(
                    material_result['output_snapshot'],
                    evidence_chunks_material,
                    'material',
                    script_id,
                    id_mapping=id_mapping,
                )
            
            # B1: Image Generation Stage (optional, after Material Generator)
            generated_images = []
            if self.enable_image_generation and self.image_generation_service and self.image_generation_service.is_enabled():
                try:
                    generated_images = self.image_generation_service.generate_instructional_visuals(
                        spec=spec,
                        planner_output=planner_result['output_snapshot'],
                        script_id=script_id
                    )
                    if generated_images:
                        logger.info(f"[Pipeline] Generated {len(generated_images)} images for run {run_id}")
                        # Add generated images to material output
                        material_result['output_snapshot']['generated_images'] = [
                            {
                                'image_id': img['image_id'],
                                'filename': img['filename'],
                                'purpose': img['metadata'].get('purpose', 'general'),
                                'target': img['metadata'].get('target', 'general'),
                                'revised_prompt': img.get('revised_prompt', '')
                            }
                            for img in generated_images
                        ]
                        material_result['generated_images_count'] = len(generated_images)
                    else:
                        logger.info(f"[Pipeline] No images generated for run {run_id}")
                except Exception as e:
                    logger.error(f"[Pipeline] Image generation error: {str(e)}")
            
            # Chart generation: embed matplotlib-based example charts
            try:
                from app.services.chart_generation_service import generate_activity_charts
                activity_charts = generate_activity_charts(spec, planner_result.get('output_snapshot') or {})
                if activity_charts:
                    material_result['output_snapshot']['activity_charts'] = activity_charts
                    logger.info(f"[Pipeline] Embedded {len(activity_charts)} activity charts for run {run_id}")
            except Exception as e:
                logger.warning(f"[Pipeline] Chart generation skipped: {e}")
            
            # Stage 3: Critic (with RAG retrieval)
            evidence_chunks_critic = self._retrieve_evidence(spec, 'critic', script_id) if self.retriever else []
            critic_options = (options or {}).copy()
            critic_options['run_id'] = run_id
            critic_result = self.critic.run(material_result['output_snapshot'], spec, critic_options)
            critic_result['retrieved_chunks_count'] = len(evidence_chunks_critic)
            critic_result['retrieved_chunk_ids'] = [c['chunk_id'] for c in evidence_chunks_critic]
            stages.append(critic_result)
            self._save_stage_run(run_id, critic_result)
            
            # If critic fails, skip refiner and use material output as final
            # (critic timeout / provider errors should not block the whole pipeline)
            critic_failed = critic_result.get('status') != 'success'
            if critic_failed:
                logger.warning(
                    "pipeline run_id=%s critic failed (%s), skipping refiner, using material output",
                    run_id, critic_result.get('error', 'unknown')
                )
                final_output = material_result.get('output_snapshot') or {}
                evidence_binding_ratio = self._compute_evidence_binding_ratio(
                    script_id, final_output
                )
                quality_report = compute_quality_report(
                    final_output, spec, evidence_binding_ratio=evidence_binding_ratio
                )
                if 'grounding' in quality_report:
                    quality_report['grounding']['status'] = grounding_status if has_docs else 'no_course_docs'
                provider_name = planner_result.get('provider', 'unknown')
                model_name = planner_result.get('model', 'unknown')
                config_fingerprint = compute_config_fingerprint(options, provider_name, model_name)
                pipeline_run.status = 'success'
                pipeline_run.config_fingerprint = config_fingerprint
                pipeline_run.final_output_json = final_output
                pipeline_run.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'run_id': run_id,
                    'status': 'success',
                    'stages': stages,
                    'final_output': final_output,
                    'quality_report': quality_report,
                    'grounding_status': grounding_status,
                    'error': None,
                    'warnings': [f'Critic stage failed ({critic_result.get("error", "timeout")}), refiner skipped. Output is from material stage.']
                }
            
            # Stage 4: Refiner (with RAG retrieval)
            evidence_chunks_refiner = self._retrieve_evidence(spec, 'refiner', script_id) if self.retriever else []
            refiner_options = (options or {}).copy()
            refiner_options['run_id'] = run_id
            refiner_result = self.refiner.run(critic_result['output_snapshot'], spec, refiner_options)
            refiner_result['retrieved_chunks_count'] = len(evidence_chunks_refiner)
            refiner_result['retrieved_chunk_ids'] = [c['chunk_id'] for c in evidence_chunks_refiner]
            stages.append(refiner_result)
            self._save_stage_run(run_id, refiner_result)
            
            if refiner_result['status'] != 'success':
                pipeline_run.status = 'partial_failed'
                pipeline_run.error_message = f"Refiner failed: {refiner_result.get('error')}"
                pipeline_run.finished_at = datetime.now(timezone.utc)
                db.session.commit()
                return {
                    'run_id': run_id,
                    'status': 'partial_failed',
                    'stages': stages,
                    'final_output': critic_result.get('output_snapshot'),
                    'quality_report': None,
                    'grounding_status': grounding_status,
                    'error': refiner_result.get('error')
                }
            
            # Add evidence refs to refiner output (same id_mapping as material)
            if evidence_chunks_refiner:
                self._add_evidence_refs_to_output(
                    refiner_result['output_snapshot'],
                    evidence_chunks_refiner,
                    'refiner',
                    script_id,
                    id_mapping=id_mapping,
                )
            
            # Compute evidence binding ratio
            evidence_binding_ratio = self._compute_evidence_binding_ratio(
                script_id, refiner_result['output_snapshot']
            )
            
            # Compute quality report
            quality_report = compute_quality_report(
                refiner_result['output_snapshot'], 
                spec,
                evidence_binding_ratio=evidence_binding_ratio
            )
            
            # Update grounding metrics
            if 'grounding' in quality_report:
                quality_report['grounding']['status'] = grounding_status if has_docs else 'no_course_docs'
            
            # Compute config fingerprint
            provider_name = planner_result.get('provider', 'unknown')
            model_name = planner_result.get('model', 'unknown')
            config_fingerprint = compute_config_fingerprint(options, provider_name, model_name)
            
            # Commit evidence bindings
            db.session.flush()
            
            final_output = dict(refiner_result['output_snapshot']) if refiner_result.get('output_snapshot') else {}
            # Pass through classroom-ready artefacts from material stage if refiner did not include them
            mat_snap = material_result.get('output_snapshot') or {}
            for _key in ('student_worksheet', 'student_slides', 'teacher_guide', 'role_cards', 'activity_charts'):
                if mat_snap.get(_key) and not final_output.get(_key):
                    final_output[_key] = mat_snap[_key]

            # Update pipeline run and persist final_output
            pipeline_run.status = 'success'
            pipeline_run.config_fingerprint = config_fingerprint
            pipeline_run.final_output_json = final_output
            pipeline_run.finished_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return {
                'run_id': run_id,
                'status': 'success',
                'stages': stages,
                'final_output': final_output,
                'quality_report': quality_report,
                'grounding_status': grounding_status,
                'error': None
            }
        except Exception as e:
            db.session.rollback()
            try:
                run_obj = CSCLPipelineRun.query.filter_by(run_id=run_id).first()
                if run_obj:
                    run_obj.status = 'failed'
                    run_obj.error_message = str(e)[:1000]
                    run_obj.finished_at = datetime.now(timezone.utc)
                    db.session.commit()
            except Exception:
                db.session.rollback()
            return {
                'run_id': run_id,
                'status': 'failed',
                'stages': stages if 'stages' in locals() else [],
                'final_output': None,
                'quality_report': None,
                'grounding_status': grounding_status if 'grounding_status' in locals() else 'no_course_docs',
                'error': str(e)
            }
    
    def _compute_evidence_binding_ratio(self, script_id: str, output: Dict[str, Any]) -> float:
        """Compute ratio of scriptlets with evidence bindings"""
        total_scriptlets = 0
        bound_scriptlets = 0
        
        scenes = output.get('scenes', [])
        for scene in scenes:
            scriptlets = scene.get('scriptlets', [])
            total_scriptlets += len(scriptlets)
            
            for scriptlet in scriptlets:
                evidence_refs = scriptlet.get('evidence_refs', [])
                if evidence_refs:
                    bound_scriptlets += 1
        
        if total_scriptlets == 0:
            return 0.0
        
        return bound_scriptlets / total_scriptlets
    
    def _save_stage_run(self, run_id: str, stage_result: Dict[str, Any]):
        """Save stage run to database"""
        try:
            stage_run = CSCLPipelineStageRun(
                run_id=run_id,
                stage_name=stage_result['stage_name'],
                input_json=stage_result.get('input_snapshot'),
                output_json=stage_result.get('output_snapshot'),
                provider=stage_result.get('provider'),
                model=stage_result.get('model'),
                latency_ms=stage_result.get('latency_ms'),
                token_usage_json=stage_result.get('token_usage'),
                status=stage_result['status'],
                error_message=stage_result.get('error')
            )
            db.session.add(stage_run)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log error but don't fail pipeline
            import logging
            logging.error(f"Failed to save stage run: {e}")
