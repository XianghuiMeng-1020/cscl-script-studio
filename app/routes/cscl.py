"""CSCL Script routes"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from app.db import db
from app.models import CSCLScript, CSCLScene, CSCLRole, CSCLScriptlet, CSCLScriptRevision, CSCLPipelineRun, CSCLPipelineStageRun, CSCLCourseDocument, CSCLEvidenceBinding, CSCLDocumentChunk, CSCLTeacherDecision, StudentGroup, CSCLCourseFolder
from app.auth import role_required, log_audit
from app.services.script_template_service import ScriptTemplateService
from app.services.cscl_llm_provider import get_cscl_llm_provider
from app.services.rag_service import RAGService
from app.services.spec_validator import SpecValidator
from app.services.cscl_pipeline_service import CSCLPipelineService
from app.services.document_service import DocumentService, is_probably_pdf_binary_text, safe_preview_or_none, to_display_safe_preview
from app.services.decision_summary_service import DecisionSummaryService
from app.services.decision_tracking_helper import create_decision_auto, detect_edits_and_create_decisions
from app.services.quality_report_service import QualityReportService
from app.services.task_type_config import get_task_types_for_api
from app.services.cscl_llm_provider import select_runnable_provider
from datetime import datetime
import json
import secrets

cscl_bp = Blueprint('cscl', __name__, url_prefix='/api/cscl')


@cscl_bp.route('/spec/validate', methods=['POST'])
def validate_spec():
    """
    Validate pedagogical specification
    
    Access control:
    - If SPEC_VALIDATE_PUBLIC=false (default): teacher/admin only
    - If SPEC_VALIDATE_PUBLIC=true: public access (development only)
    """
    from app.config import Config
    spec_validate_public = current_app.config.get('SPEC_VALIDATE_PUBLIC', Config.SPEC_VALIDATE_PUBLIC)
    # Check if public access is enabled
    if not spec_validate_public:
        # Require authentication and teacher/admin role
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        user_role = current_user.role.value if current_user.role else None
        if user_role not in ['teacher', 'admin']:
            return jsonify({
                'error': 'Insufficient permissions',
                'code': 'PERMISSION_DENIED',
                'required_roles': ['teacher', 'admin'],
                'user_role': user_role
            }), 403
    
    # Parse JSON (400 for JSON parsing errors)
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({
            'valid': False,
            'issues': [f'Invalid JSON: {str(e)}'],
            'normalized_spec': None,
            'code': 'INVALID_JSON'
        }), 400
    
    if data is None:
        return jsonify({
            'valid': False,
            'issues': ['Request body must contain JSON data'],
            'normalized_spec': None,
            'code': 'MISSING_BODY'
        }), 400
    
    # Validate spec (422 for validation errors)
    try:
        result = SpecValidator.validate(data)
        
        if result['valid']:
            return jsonify(result), 200
        else:
            # Business rule validation failures -> 422
            return jsonify({
                **result,
                'code': 'VALIDATION_FAILED'
            }), 422
    except Exception as e:
        current_app.logger.error(f"Error validating spec: {e}")
        return jsonify({
            'valid': False,
            'issues': [f'Validation error: {str(e)}'],
            'normalized_spec': None,
            'code': 'INTERNAL_ERROR'
        }), 500


@cscl_bp.route('/task-types', methods=['GET'])
def get_task_types():
    """Return task type config (v1 argumentation-oriented taxonomy) for UI and validation alignment."""
    return jsonify(get_task_types_for_api()), 200


@cscl_bp.route('/scripts', methods=['POST'])
@role_required('teacher', 'admin')
def create_script():
    """Create a new CSCL script (teacher/admin only)"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('topic') or not data.get('title'):
        return jsonify({'error': 'topic and title are required'}), 400
    
    # Generate template if requested
    template = None
    if data.get('generate_template', False):
        objectives = data.get('learning_objectives', [])
        duration = data.get('duration_minutes', 60)
        task_type = data.get('task_type', 'structured_debate')
        template = ScriptTemplateService.generate_template(
            data['topic'],
            objectives,
            duration,
            task_type
        )
    
    # Create script
    script = CSCLScript(
        title=data.get('title', ''),
        topic=data.get('topic', ''),
        course_id=data.get('course_id'),
        learning_objectives=data.get('learning_objectives', []),
        task_type=data.get('task_type', 'structured_debate'),
        duration_minutes=data.get('duration_minutes', 60),
        status='draft',
        created_by=current_user.id
    )
    db.session.add(script)
    db.session.flush()  # Get script.id
    
    # Create scenes and roles from template if provided
    if template:
        # Create roles
        role_map = {}
        for role_data in template['roles']:
            role = CSCLRole(
                script_id=script.id,
                role_name=role_data['role_name'],
                responsibilities=role_data['responsibilities']
            )
            db.session.add(role)
            db.session.flush()
            role_map[role_data['role_name']] = role.id
        
        # Create scenes and scriptlets
        for scene_data in template['scenes']:
            scene = CSCLScene(
                script_id=script.id,
                order_index=scene_data['order_index'],
                scene_type=scene_data['scene_type'],
                purpose=scene_data['purpose'],
                transition_rule=scene_data['transition_rule']
            )
            db.session.add(scene)
            db.session.flush()
            
            # Create scriptlets for this scene
            for scriptlet_data in scene_data.get('scriptlets', []):
                scriptlet = CSCLScriptlet(
                    scene_id=scene.id,
                    role_id=scriptlet_data.get('role_id'),
                    prompt_text=scriptlet_data['prompt_text'],
                    prompt_type=scriptlet_data['prompt_type'],
                    resource_ref=scriptlet_data.get('resource_ref')
                )
                db.session.add(scriptlet)
    
    db.session.commit()
    
    # Log revision
    _log_script_revision(script.id, current_user.id, 'create', None, script.to_dict(), 'Script created')
    
    log_audit(
        'script_create',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script.id,
        status='success'
    )
    
    return jsonify({
        'success': True,
        'script': script.to_dict()
    }), 201


@cscl_bp.route('/scripts', methods=['GET'])
@role_required('teacher', 'admin')
def list_scripts():
    """List all CSCL scripts (teacher/admin only)"""
    scripts = CSCLScript.query.filter_by(created_by=current_user.id).all()
    return jsonify({
        'success': True,
        'scripts': [s.to_dict() for s in scripts]
    }), 200


@cscl_bp.route('/scripts/<script_id>', methods=['GET'])
@role_required('teacher', 'admin')
def get_script(script_id):
    """Get a specific CSCL script with full structure (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    # Load full structure
    scenes = CSCLScene.query.filter_by(script_id=script_id).order_by(CSCLScene.order_index).all()
    roles = CSCLRole.query.filter_by(script_id=script_id).all()
    
    script_dict = script.to_dict()
    script_dict['scenes'] = []
    
    for scene in scenes:
        scene_dict = scene.to_dict()
        scriptlets = CSCLScriptlet.query.filter_by(scene_id=scene.id).all()
        scene_dict['scriptlets'] = [s.to_dict() for s in scriptlets]
        script_dict['scenes'].append(scene_dict)
    
    script_dict['roles'] = [r.to_dict() for r in roles]
    
    return jsonify({
        'success': True,
        'script': script_dict
    }), 200


@cscl_bp.route('/scripts/<script_id>', methods=['PUT'])
@role_required('teacher', 'admin')
def update_script(script_id):
    """Update a CSCL script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    data = request.get_json()
    
    # Update script fields
    if 'title' in data:
        script.title = data['title']
    if 'topic' in data:
        script.topic = data['topic']
    if 'course_id' in data:
        script.course_id = data['course_id']
    if 'learning_objectives' in data:
        script.learning_objectives = data['learning_objectives']
    if 'task_type' in data:
        script.task_type = data['task_type']
    if 'duration_minutes' in data:
        script.duration_minutes = data['duration_minutes']
    
    before_state = script.to_dict()
    script.updated_at = datetime.utcnow()
    db.session.commit()
    after_state = script.to_dict()
    
    # Log revision
    revision = _log_script_revision(script_id, current_user.id, 'update', before_state, after_state, 'Script updated')
    
    # Auto-detect edits and create decisions
    if revision:
        detect_edits_and_create_decisions(
            script_id=script_id,
            actor_id=current_user.id,
            before_state=before_state,
            after_state=after_state,
            revision_id=revision.id,
            source_stage='manual'
        )
        db.session.commit()
    
    log_audit(
        'script_update',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success'
    )
    
    return jsonify({
        'success': True,
        'script': script.to_dict()
    }), 200


@cscl_bp.route('/scripts/<script_id>/finalize', methods=['POST'])
@role_required('teacher', 'admin')
def finalize_script(script_id):
    """Finalize a CSCL script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    before_state = script.to_dict()
    script.status = 'final'
    script.updated_at = datetime.utcnow()
    db.session.commit()
    after_state = script.to_dict()
    
    # Log revision
    revision = _log_script_revision(script_id, current_user.id, 'finalize', before_state, after_state, 'Script finalized')
    
    # Auto-detect edits and create decisions
    if revision:
        detect_edits_and_create_decisions(
            script_id=script_id,
            actor_id=current_user.id,
            before_state=before_state,
            after_state=after_state,
            revision_id=revision.id,
            source_stage='manual'
        )
    
    # Create finalize_note decision
    create_decision_auto(
        script_id=script_id,
        actor_id=current_user.id,
        decision_type='finalize_note',
        target_type='pipeline_output',
        revision_id=revision.id if revision else None,
        source_stage='manual',
        rationale_text='Script finalized'
    )
    
    db.session.commit()
    
    log_audit(
        'script_finalize',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success'
    )
    
    return jsonify({
        'success': True,
        'script': script.to_dict()
    }), 200


def _generate_share_code():
    """Generate a 6-character alphanumeric share code (uppercase for readability)."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # avoid ambiguous 0/O, 1/I
    return ''.join(secrets.choice(alphabet) for _ in range(6))


@cscl_bp.route('/scripts/<script_id>/publish', methods=['POST'])
@role_required('teacher', 'admin')
def publish_script(script_id):
    """Publish a script for students: set published_at, generate share_code, create one StudentGroup. Returns share_code and student_url."""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    if script.published_at:
        return jsonify({
            'share_code': script.share_code,
            'student_url': request.host_url.rstrip('/') + '/student?code=' + (script.share_code or ''),
            'already_published': True
        }), 200
    share_code = _generate_share_code()
    while CSCLScript.query.filter_by(share_code=share_code).first():
        share_code = _generate_share_code()
    script.published_at = datetime.utcnow()
    script.share_code = share_code
    script.updated_at = datetime.utcnow()
    group = StudentGroup(script_id=script.id, group_name=f'Group for {script.title[:50]}')
    db.session.add(group)
    db.session.commit()
    student_url = request.host_url.rstrip('/') + '/student?code=' + share_code
    log_audit(
        'script_publish',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success'
    )
    return jsonify({
        'success': True,
        'share_code': share_code,
        'student_url': student_url,
        'script': script.to_dict()
    }), 200


def _build_worksheet_teacher_guide_html(script_title: str, student_worksheet: dict, teacher_guide: dict) -> str:
    """Build a single HTML document with student worksheet and teacher guide (print-ready)."""
    sw = student_worksheet or {}
    tg = teacher_guide or {}
    html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>{}</title>'.format(script_title or 'CSCL Activity'),
            '<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:1.5rem;line-height:1.5;}',
            'h1,h2,h3{color:#333;} .section{margin-bottom:2rem;} .step{margin-bottom:1rem;padding-bottom:0.75rem;border-bottom:1px solid #eee;}',
            '.teacher-section{background:#f8f9fa;padding:1rem;border-radius:8px;margin-top:2rem;}</style></head><body>']
    html.append('<h1>{}</h1>'.format(sw.get('title') or script_title or 'Activity'))
    if sw.get('goal'):
        html.append('<p><strong>Goal:</strong> {}</p>'.format(_escape_html(str(sw['goal']))))
    if sw.get('roles_summary'):
        html.append('<div class="section"><h2>Roles</h2><p>{}</p></div>'.format(_escape_html(str(sw['roles_summary']))))
    if sw.get('steps'):
        html.append('<div class="section"><h2>Steps</h2>')
        for s in sw['steps']:
            html.append('<div class="step"><strong>Step {}: {}</strong>'.format(s.get('step_order', ''), _escape_html(str(s.get('title', '')))))
            if s.get('duration_minutes'):
                html.append(' <span>({} min)</span>'.format(s['duration_minutes']))
            if s.get('description'):
                html.append('<p>{}</p>'.format(_escape_html(str(s['description']))))
            if s.get('prompts'):
                html.append('<ul>')
                for p in s['prompts']:
                    html.append('<li>{}</li>'.format(_escape_html(str(p))))
                html.append('</ul>')
            html.append('</div>')
        html.append('</div>')
    if sw.get('output_instructions'):
        html.append('<div class="section"><h2>Expected output</h2><p>{}</p></div>'.format(_escape_html(str(sw['output_instructions']))))
    if sw.get('reporting_instructions'):
        html.append('<p>{}</p>'.format(_escape_html(str(sw['reporting_instructions']))))
    html.append('<hr/><div class="teacher-section"><h2>Teacher guide</h2>')
    if tg.get('overview'):
        html.append('<h3>Overview</h3><p>{}</p>'.format(_escape_html(str(tg['overview']))))
    if tg.get('rationale'):
        html.append('<h3>Rationale</h3><p>{}</p>'.format(_escape_html(str(tg['rationale']))))
    if tg.get('implementation_steps'):
        html.append('<h3>Implementation</h3><p>{}</p>'.format(_escape_html(str(tg['implementation_steps']))))
    if tg.get('monitoring_points'):
        html.append('<h3>Monitoring</h3><p>{}</p>'.format(_escape_html(str(tg['monitoring_points']))))
    if tg.get('debrief_questions'):
        html.append('<h3>Debrief questions</h3><p>{}</p>'.format(_escape_html(str(tg['debrief_questions']))))
    html.append('</div></body></html>')
    return '\n'.join(html)


def _build_worksheet_teacher_guide_markdown(script_title: str, student_worksheet: dict, teacher_guide: dict) -> str:
    """Build Markdown string for student worksheet and teacher guide."""
    sw = student_worksheet or {}
    tg = teacher_guide or {}
    lines = ['# {}\n'.format(sw.get('title') or script_title or 'Activity')]
    if sw.get('goal'):
        lines.append('**Goal:** {}\n'.format(sw['goal']))
    if sw.get('roles_summary'):
        lines.append('## Roles\n\n{}\n'.format(sw['roles_summary']))
    if sw.get('steps'):
        lines.append('## Steps\n')
        for s in sw['steps']:
            lines.append('### Step {}: {}'.format(s.get('step_order', ''), s.get('title', '')))
            if s.get('duration_minutes'):
                lines.append(' ({} min)'.format(s['duration_minutes']))
            lines.append('\n')
            if s.get('description'):
                lines.append('{}\n'.format(s['description']))
            if s.get('prompts'):
                for p in s['prompts']:
                    lines.append('- {}\n'.format(p))
        lines.append('')
    if sw.get('output_instructions'):
        lines.append('## Expected output\n\n{}\n'.format(sw['output_instructions']))
    if sw.get('reporting_instructions'):
        lines.append('{}\n'.format(sw['reporting_instructions']))
    lines.append('\n---\n\n# Teacher guide\n')
    if tg.get('overview'):
        lines.append('## Overview\n\n{}\n'.format(tg['overview']))
    if tg.get('rationale'):
        lines.append('## Rationale\n\n{}\n'.format(tg['rationale']))
    if tg.get('implementation_steps'):
        lines.append('## Implementation\n\n{}\n'.format(tg['implementation_steps']))
    if tg.get('monitoring_points'):
        lines.append('## Monitoring\n\n{}\n'.format(tg['monitoring_points']))
    if tg.get('debrief_questions'):
        lines.append('## Debrief questions\n\n{}\n'.format(tg['debrief_questions']))
    return ''.join(lines)


def _escape_html(s: str) -> str:
    if not s:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


@cscl_bp.route('/scripts/<script_id>/export', methods=['GET'])
@role_required('teacher', 'admin')
def export_script(script_id):
    """Export a CSCL script as JSON (default), HTML, or Markdown (teacher/admin only). Use ?format=html or ?format=markdown."""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404

    export_format = (request.args.get('format') or 'json').strip().lower()
    if export_format in ('html', 'markdown'):
        latest_run = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
            CSCLPipelineRun.created_at.desc()
        ).first()
        pipeline_output = None
        if latest_run:
            for stage_name in ('refiner', 'material_generator', 'critic', 'planner'):
                stage_run = CSCLPipelineStageRun.query.filter_by(
                    run_id=latest_run.run_id, stage_name=stage_name, status='success'
                ).order_by(CSCLPipelineStageRun.created_at.desc()).first()
                if stage_run and stage_run.output_json:
                    pipeline_output = stage_run.output_json
                    if pipeline_output.get('student_worksheet') or pipeline_output.get('teacher_guide'):
                        break
        if not pipeline_output or (not pipeline_output.get('student_worksheet') and not pipeline_output.get('teacher_guide')):
            return jsonify({
                'error': 'No classroom-ready materials (student_worksheet/teacher_guide) found. Run the pipeline first.'
            }), 404
        title = (script.title or script.topic or 'Activity').replace('/', '-')
        if export_format == 'html':
            body = _build_worksheet_teacher_guide_html(
                title,
                pipeline_output.get('student_worksheet'),
                pipeline_output.get('teacher_guide')
            )
            from flask import Response
            resp = Response(body, mimetype='text/html; charset=utf-8')
            resp.headers['Content-Disposition'] = 'attachment; filename="{}_activity.html"'.format(title[:50])
            return resp
        if export_format == 'markdown':
            body = _build_worksheet_teacher_guide_markdown(
                title,
                pipeline_output.get('student_worksheet'),
                pipeline_output.get('teacher_guide')
            )
            from flask import Response
            resp = Response(body, mimetype='text/markdown; charset=utf-8')
            resp.headers['Content-Disposition'] = 'attachment; filename="{}_activity.md"'.format(title[:50])
            return resp

    # Load full structure (JSON export)
    scenes = CSCLScene.query.filter_by(script_id=script_id).order_by(CSCLScene.order_index).all()
    roles = CSCLRole.query.filter_by(script_id=script_id).all()
    
    # Load evidence bindings
    evidence_bindings = CSCLEvidenceBinding.query.filter_by(script_id=script_id).all()
    
    # Build chunk_id -> evidence_details mapping
    chunk_details_map = {}
    for binding in evidence_bindings:
        chunk_id = binding.chunk_id
        if chunk_id not in chunk_details_map:
            chunk = CSCLDocumentChunk.query.get(chunk_id)
            if chunk:
                doc = CSCLCourseDocument.query.get(chunk.document_id)
                snippet = safe_preview_or_none(chunk.chunk_text or '', 300) if chunk.chunk_text else ''
                chunk_details_map[chunk_id] = {
                    'chunk_id': chunk_id,
                    'doc_id': chunk.document_id,
                    'doc_title': doc.title if doc else 'Unknown',
                    'snippet': snippet if snippet is not None else '',
                    'relevance_score': binding.relevance_score,
                    'binding_type': binding.binding_type
                }
    
    # Build scriptlet_id -> evidence_refs mapping
    scriptlet_evidence_map = {}
    scene_evidence_map = {}
    for binding in evidence_bindings:
        if binding.scriptlet_id:
            if binding.scriptlet_id not in scriptlet_evidence_map:
                scriptlet_evidence_map[binding.scriptlet_id] = []
            scriptlet_evidence_map[binding.scriptlet_id].append(binding.chunk_id)
        
        if binding.scene_id:
            if binding.scene_id not in scene_evidence_map:
                scene_evidence_map[binding.scene_id] = []
            scene_evidence_map[binding.scene_id].append(binding.chunk_id)
    
    export_data = script.to_dict()
    export_data['scenes'] = []
    
    total_scriptlets = 0
    bound_scriptlets = 0
    
    for scene in scenes:
        scene_dict = scene.to_dict()
        
        # Add scene-level evidence_refs
        scene_evidence_refs = list(set(scene_evidence_map.get(scene.id, [])))
        scene_dict['evidence_refs'] = scene_evidence_refs
        scene_dict['evidence_details'] = [
            chunk_details_map[chunk_id] for chunk_id in scene_evidence_refs 
            if chunk_id in chunk_details_map
        ]
        
        scriptlets = CSCLScriptlet.query.filter_by(scene_id=scene.id).all()
        scriptlet_dicts = []
        
        for scriptlet in scriptlets:
            scriptlet_dict = scriptlet.to_dict()
            
            # Add scriptlet-level evidence_refs
            scriptlet_evidence_refs = list(set(scriptlet_evidence_map.get(scriptlet.id, [])))
            scriptlet_dict['evidence_refs'] = scriptlet_evidence_refs
            scriptlet_dict['evidence_details'] = [
                chunk_details_map[chunk_id] for chunk_id in scriptlet_evidence_refs 
                if chunk_id in chunk_details_map
            ]
            
            scriptlet_dicts.append(scriptlet_dict)
            
            total_scriptlets += 1
            if scriptlet_evidence_refs:
                bound_scriptlets += 1
        
        scene_dict['scriptlets'] = scriptlet_dicts
        export_data['scenes'].append(scene_dict)
    
    export_data['roles'] = [r.to_dict() for r in roles]
    
    # Compute evidence_coverage
    evidence_coverage = bound_scriptlets / total_scriptlets if total_scriptlets > 0 else 0.0
    
    # Add evidence metadata
    export_data['evidence_metadata'] = {
        'evidence_coverage': evidence_coverage,
        'total_scriptlets': total_scriptlets,
        'bound_scriptlets': bound_scriptlets,
        'total_evidence_chunks': len(chunk_details_map)
    }
    
    # Check for missing references (orphaned bindings)
    missing_refs = []
    for binding in evidence_bindings:
        chunk_id = binding.chunk_id
        if chunk_id not in chunk_details_map:
            missing_refs.append({
                'binding_id': binding.id,
                'chunk_id': chunk_id,
                'scriptlet_id': binding.scriptlet_id,
                'scene_id': binding.scene_id
            })
    
    if missing_refs:
        export_data['evidence_warnings'] = {
            'missing_references': missing_refs,
            'message': f'Found {len(missing_refs)} evidence bindings with missing chunk references'
        }
    
    log_audit(
        'script_export',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success'
    )
    
    return jsonify({
        'success': True,
        'script': export_data
    }), 200


def _log_script_revision(script_id: str, editor_id: str, revision_type: str, 
                         before_json: dict, after_json: dict, diff_summary: str):
    """Helper function to log script revision"""
    try:
        if not current_app.config.get('USE_DB_STORAGE', False):
            return None
        
        revision = CSCLScriptRevision(
            script_id=script_id,
            editor_id=editor_id,
            revision_type=revision_type,
            before_json=before_json,
            after_json=after_json,
            diff_summary=diff_summary
        )
        db.session.add(revision)
        db.session.flush()
        return revision
    except Exception as e:
        current_app.logger.error(f"Failed to log script revision: {e}")
        db.session.rollback()
        return None


@cscl_bp.route('/scripts/<script_id>/generate-ai', methods=['POST'])
@role_required('teacher', 'admin')
def generate_ai_script(script_id):
    """Generate AI suggestions for script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    # Get RAG chunks
    rag_service = RAGService()
    retrieved_chunks = rag_service.retrieve_chunks(
        script.topic,
        script.learning_objectives or [],
        script.course_id
    )
    
    # Prepare input for LLM provider
    input_payload = {
        'topic': script.topic,
        'learning_objectives': script.learning_objectives or [],
        'task_type': script.task_type,
        'duration_minutes': script.duration_minutes,
        'retrieved_chunks': retrieved_chunks
    }
    
    # Get provider
    provider = get_cscl_llm_provider()
    result = provider.generate_script_plan(input_payload)
    
    if not result.get('success'):
        error_msg = result.get('error', 'Unknown error')
        error_code = 503 if 'not configured' in error_msg.lower() else 400
        return jsonify({
            'success': False,
            'error': error_msg,
            'code': 'PROVIDER_ERROR',
            'provider': result.get('provider', 'unknown')
        }), error_code
    
    log_audit(
        'script_ai_generate',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success',
        meta={'provider': result.get('provider')}
    )
    
    # Create candidate snapshot decisions for AI-generated content
    plan = result.get('plan', {})
    scenes = plan.get('scenes', [])
    roles = plan.get('roles', [])
    
    for scene in scenes:
        create_decision_auto(
            script_id=script_id,
            actor_id=current_user.id,
            decision_type='accept',  # Candidate for acceptance
            target_type='scene',
            target_id=scene.get('id'),
            after_json=scene,
            source_stage='planner',
            rationale_text='AI-generated candidate from planner stage'
        )
    
    for role in roles:
        create_decision_auto(
            script_id=script_id,
            actor_id=current_user.id,
            decision_type='accept',  # Candidate for acceptance
            target_type='role',
            target_id=role.get('id'),
            after_json=role,
            source_stage='planner',
            rationale_text='AI-generated candidate from planner stage'
        )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'plan': result['plan'],
        'provider': result['provider'],
        'model': result['model'],
        'retrieved_chunks': retrieved_chunks
    }), 200


@cscl_bp.route('/scripts/<script_id>/regenerate-scene', methods=['POST'])
@role_required('teacher', 'admin')
def regenerate_scene(script_id):
    """Regenerate a specific scene using AI (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    data = request.get_json()
    scene_id = data.get('scene_id')
    instruction = data.get('instruction', 'Regenerate this scene')
    
    if not scene_id:
        return jsonify({'error': 'scene_id is required'}), 400
    
    scene = CSCLScene.query.filter_by(id=scene_id, script_id=script_id).first()
    if not scene:
        return jsonify({'error': 'Scene not found'}), 404
    
    # Get RAG chunks
    rag_service = RAGService()
    retrieved_chunks = rag_service.retrieve_chunks(
        script.topic,
        script.learning_objectives or [],
        script.course_id
    )
    
    # Prepare input for provider
    input_payload = {
        'topic': script.topic,
        'learning_objectives': script.learning_objectives or [],
        'task_type': script.task_type,
        'duration_minutes': script.duration_minutes,
        'retrieved_chunks': retrieved_chunks,
        'scene_type': scene.scene_type,
        'instruction': instruction
    }
    
    # Get provider
    provider = get_cscl_llm_provider()
    result = provider.generate_script_plan(input_payload)
    
    if not result.get('success'):
        error_msg = result.get('error', 'Unknown error')
        error_code = 503 if 'not configured' in error_msg.lower() else 400
        return jsonify({
            'success': False,
            'error': error_msg,
            'code': 'PROVIDER_ERROR',
            'provider': result.get('provider', 'unknown')
        }), error_code
    
    # Extract scene from plan (use first scene matching type, or first scene)
    plan_scenes = result['plan'].get('scenes', [])
    new_scene_data = None
    for plan_scene in plan_scenes:
        if plan_scene.get('scene_type') == scene.scene_type:
            new_scene_data = plan_scene
            break
    
    if not new_scene_data and plan_scenes:
        new_scene_data = plan_scenes[0]
    
    # Log revision
    before_state = scene.to_dict()
    if new_scene_data:
        scene.purpose = new_scene_data.get('purpose', scene.purpose)
        scene.transition_rule = new_scene_data.get('transition_rule', scene.transition_rule)
        db.session.commit()
        after_state = scene.to_dict()
        _log_script_revision(script_id, current_user.id, 'regenerate', before_state, after_state, f'Scene regenerated: {instruction}')
    
    log_audit(
        'script_regenerate',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success',
        meta={'scene_id': scene_id, 'provider': result.get('provider')}
    )
    
    return jsonify({
        'success': True,
        'scene': scene.to_dict() if new_scene_data else before_state,
        'provider': result['provider'],
        'model': result['model']
    }), 200


@cscl_bp.route('/scripts/<script_id>/revisions', methods=['GET'])
@role_required('teacher', 'admin')
def get_script_revisions(script_id):
    """Get revision history for a script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    revisions = CSCLScriptRevision.query.filter_by(script_id=script_id).order_by(
        CSCLScriptRevision.created_at.desc()
    ).all()
    
    log_audit(
        'script_revision_view',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success'
    )
    
    return jsonify({
        'success': True,
        'revisions': [r.to_dict() for r in revisions]
    }), 200


@cscl_bp.route('/courses/<course_id>/docs/upload', methods=['POST'])
@role_required('teacher', 'admin')
def upload_course_document(course_id):
    """Upload a course document (teacher/admin only)"""
    document_service = DocumentService()
    
    # Check if file upload or text content
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'code': 'NO_FILE'
            }), 400
        
        title = request.form.get('title', file.filename)
        file_content = file.read()
        filename = file.filename
        mime_type = file.content_type or 'application/octet-stream'
        material_level = request.form.get('material_level', 'course')
        if material_level not in ('course', 'lesson'):
            material_level = 'course'
        extract_text = (request.form.get('extract_text', 'true') or 'true').strip().lower() not in ('false', '0', 'no')
        folder_id = request.form.get('folder_id') or None
        
        result = document_service.upload_document(
            course_id=course_id,
            title=title,
            file_content=file_content,
            filename=filename,
            mime_type=mime_type,
            uploaded_by=current_user.id,
            material_level=material_level,
            extract_text=extract_text,
            folder_id=folder_id
        )
    elif request.is_json:
        data = request.get_json()
        title = data.get('title')
        text = data.get('text')
        material_level = data.get('material_level', 'course')
        if material_level not in ('course', 'lesson'):
            material_level = 'course'
        
        if not title or not text:
            return jsonify({
                'error': 'title and text are required',
                'code': 'MISSING_FIELDS'
            }), 400
        
        folder_id = data.get('folder_id') or None
        
        result = document_service.upload_text_document(
            course_id=course_id,
            title=title,
            text=text,
            uploaded_by=current_user.id,
            material_level=material_level,
            folder_id=folder_id
        )
    else:
        return jsonify({
            'error': 'Either file upload or JSON with text content required',
            'code': 'INVALID_REQUEST'
        }), 400
    
    if result['error']:
        # Map error codes to HTTP status codes
        error_code = result.get('error_code', 'UPLOAD_FAILED')
        
        if error_code == 'PDF_PARSE_FAILED':
            return jsonify({
                'error': 'PDF_PARSE_FAILED',
                'code': 'PDF_PARSE_FAILED',
                'message': 'Unable to parse readable text from PDF. Please upload a text-based PDF or paste plain text.'
            }), 422
        elif error_code == 'UNSUPPORTED_FILE_TYPE':
            return jsonify({
                'error': result['error'],
                'code': 'UNSUPPORTED_FILE_TYPE'
            }), 415
        elif error_code == 'TEXT_TOO_SHORT':
            return jsonify({
                'error': result['error'],
                'code': 'TEXT_TOO_SHORT'
            }), 422
        elif error_code == 'EMPTY_EXTRACTED_TEXT':
            return jsonify({
                'error': result['error'],
                'code': 'EMPTY_EXTRACTED_TEXT'
            }), 422
        elif error_code == 'FILE_TOO_LARGE':
            from app.utils.api_errors import api_error_response
            return api_error_response(
                'FILE_TOO_LARGE',
                result.get('error', 'File too large.'),
                413,
                details={'max_size_mb': 10}
            )
        elif error_code == 'EXTRACTION_TIMEOUT':
            return jsonify({
                'error': result.get('error', 'PDF extraction timed out.'),
                'code': 'EXTRACTION_TIMEOUT'
            }), 504
        else:
            return jsonify({
                'error': result['error'],
                'code': error_code
            }), 400
    
    log_audit(
        'document_upload',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=course_id,
        status='success',
        meta={'document_id': result['document']['id']}
    )
    
    meta = result.get('extraction_metadata') or {}
    doc = result['document']
    doc_id = doc['id']
    # Prefer service-provided preview (Bug 3: avoid 422 after successful commit)
    preview = meta.get('extracted_text_preview')
    from app.models import CSCLDocumentChunk
    chunks = CSCLDocumentChunk.query.filter_by(document_id=doc_id).order_by(CSCLDocumentChunk.chunk_index).all()
    full_text = '\n'.join(c.chunk_text for c in chunks if c.chunk_text and not is_probably_pdf_binary_text(c.chunk_text))
    if preview is None:
        preview = to_display_safe_preview(full_text or '')
    if preview is None:
        preview = ''
    response_data = {
        'ok': True,
        'success': True,
        'doc_id': doc_id,
        'document': doc,
        'chunks_count': result['chunks_count'],
        'detected_type': meta.get('detected_type') or ('pdf' if (doc.get('mime_type') or '').startswith('application/pdf') else 'txt'),
        'extracted_char_count': len(full_text) if full_text else meta.get('extracted_char_count', 0),
        'extracted_text_preview': preview,
        'extracted_text': full_text or '',
        'extraction_method': meta.get('extraction_method', 'plain_text'),
        'warnings': meta.get('warnings') or []
    }
    return jsonify(response_data), 201


@cscl_bp.route('/courses/<course_id>/docs', methods=['GET'])
@role_required('teacher', 'admin', 'student')
def list_course_documents(course_id):
    """List all documents for a course, optionally filtered by folder_id"""
    folder_id = request.args.get('folder_id') or None
    document_service = DocumentService()
    documents = document_service.get_course_documents(course_id, folder_id=folder_id)
    resp = jsonify({
        'success': True,
        'documents': documents,
        'count': len(documents)
    })
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return resp, 200


@cscl_bp.route('/courses/<course_id>/docs/<doc_id>', methods=['DELETE'])
@role_required('teacher', 'admin')
def delete_course_document(course_id, doc_id):
    """Delete a course document (teacher/admin only)"""
    document_service = DocumentService()
    
    success = document_service.delete_document(
        document_id=doc_id,
        course_id=course_id,
        user_id=current_user.id
    )
    
    if not success:
        return jsonify({
            'error': 'Document not found or permission denied',
            'code': 'NOT_FOUND_OR_DENIED'
        }), 404
    
    log_audit(
        'document_delete',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=course_id,
        status='success',
        meta={'document_id': doc_id}
    )
    
    return jsonify({
        'success': True,
        'message': 'Document deleted'
    }), 200


@cscl_bp.route('/courses/<course_id>/docs/<doc_id>/prefill', methods=['GET'])
@role_required('teacher', 'admin')
def doc_prefill(course_id, doc_id):
    """C3: Get suggested form fields from document text (rule-based). Teacher confirms/edits."""
    doc = CSCLCourseDocument.query.filter_by(id=doc_id, course_id=course_id).first()
    if not doc:
        return jsonify({
            'success': False,
            'error_code': 'NOT_FOUND',
            'message': 'Document not found.',
            'suggestions': {},
            'warnings': []
        }), 404
    chunks = CSCLDocumentChunk.query.filter_by(document_id=doc_id).order_by(CSCLDocumentChunk.chunk_index).all()
    # Use only safe chunks (no PDF binary) for prefill to avoid garbage suggestions
    safe_chunks = [c.chunk_text for c in chunks if c.chunk_text and not is_probably_pdf_binary_text(c.chunk_text)] if chunks else []
    full_text = ' '.join(safe_chunks) if safe_chunks else ''
    from app.services.prefill_service import extract_prefill
    result = extract_prefill(full_text)
    return jsonify({
        'success': True,
        'doc_id': doc_id,
        'suggestions': result['suggestions'],
        'warnings': result.get('warnings', []),
        'degraded': result.get('degraded', False)
    }), 200


@cscl_bp.route('/scripts/<script_id>/decisions', methods=['POST'])
@role_required('teacher', 'admin')
def create_decision(script_id):
    """Create a teacher decision record (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    data = request.get_json() or {}
    
    # Validate required fields
    decision_type = data.get('decision_type')
    target_type = data.get('target_type')
    
    if not decision_type or not target_type:
        return jsonify({
            'error': 'decision_type and target_type are required',
            'code': 'MISSING_REQUIRED_FIELDS'
        }), 400
    
    # Validate decision_type
    if decision_type not in CSCLTeacherDecision.VALID_DECISION_TYPES:
        return jsonify({
            'error': f'Invalid decision_type. Valid values: {CSCLTeacherDecision.VALID_DECISION_TYPES}',
            'code': 'INVALID_DECISION_TYPE'
        }), 422
    
    # Validate target_type
    if target_type not in CSCLTeacherDecision.VALID_TARGET_TYPES:
        return jsonify({
            'error': f'Invalid target_type. Valid values: {CSCLTeacherDecision.VALID_TARGET_TYPES}',
            'code': 'INVALID_TARGET_TYPE'
        }), 422
    
    # Validate source_stage if provided
    source_stage = data.get('source_stage')
    if source_stage and source_stage not in CSCLTeacherDecision.VALID_SOURCE_STAGES:
        return jsonify({
            'error': f'Invalid source_stage. Valid values: {CSCLTeacherDecision.VALID_SOURCE_STAGES}',
            'code': 'INVALID_SOURCE_STAGE'
        }), 422
    
    # Validate confidence if provided
    confidence = data.get('confidence')
    if confidence is not None:
        if not isinstance(confidence, int) or confidence < 1 or confidence > 5:
            return jsonify({
                'error': 'confidence must be an integer between 1 and 5',
                'code': 'INVALID_CONFIDENCE'
            }), 422
    
    # Get revision_id if provided
    revision_id = data.get('revision_id')
    if revision_id:
        revision = CSCLScriptRevision.query.filter_by(id=revision_id, script_id=script_id).first()
        if not revision:
            return jsonify({
                'error': 'Revision not found',
                'code': 'REVISION_NOT_FOUND'
            }), 404
    
    # Create decision
    decision = CSCLTeacherDecision(
        script_id=script_id,
        revision_id=revision_id,
        actor_id=current_user.id,
        decision_type=decision_type,
        target_type=target_type,
        target_id=data.get('target_id'),
        before_json=data.get('before_json'),
        after_json=data.get('after_json'),
        rationale_text=data.get('rationale_text'),
        source_stage=source_stage,
        confidence=confidence
    )
    
    db.session.add(decision)
    db.session.commit()
    
    # Generate readable summary
    summary = f"{decision_type.capitalize()} {target_type}"
    if decision.target_id:
        summary += f" (id: {decision.target_id[:8]}...)"
    if decision.source_stage:
        summary += f" from {decision.source_stage}"
    
    log_audit(
        'decision_create',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=script_id,
        status='success',
        meta={'decision_id': decision.id, 'decision_type': decision_type}
    )
    
    return jsonify({
        'success': True,
        'decision': decision.to_dict(),
        'summary': summary
    }), 201


@cscl_bp.route('/scripts/<script_id>/decisions', methods=['GET'])
@role_required('teacher', 'admin')
def list_decisions(script_id):
    """List teacher decisions for a script with filtering (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    # Get filter parameters
    decision_type = request.args.get('decision_type')
    target_type = request.args.get('target_type')
    source_stage = request.args.get('source_stage')
    actor_id = request.args.get('actor_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    # Build query
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
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            query = query.filter(CSCLTeacherDecision.created_at >= start_dt)
        except ValueError:
            return jsonify({
                'error': 'Invalid start_time format. Use ISO 8601 format.',
                'code': 'INVALID_TIME_FORMAT'
            }), 400
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            query = query.filter(CSCLTeacherDecision.created_at <= end_dt)
        except ValueError:
            return jsonify({
                'error': 'Invalid end_time format. Use ISO 8601 format.',
                'code': 'INVALID_TIME_FORMAT'
            }), 400
    
    # Order by created_at
    query = query.order_by(CSCLTeacherDecision.created_at)
    
    # Pagination
    total = query.count()
    decisions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return jsonify({
        'success': True,
        'decisions': [d.to_dict() for d in decisions],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': (total + page_size - 1) // page_size
        }
    }), 200


@cscl_bp.route('/scripts/<script_id>/decision-summary', methods=['GET'])
@role_required('teacher', 'admin')
def get_decision_summary(script_id):
    """Get decision summary metrics (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    # Get reproducibility info from latest pipeline run if available
    latest_run = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
        CSCLPipelineRun.created_at.desc()
    ).first()
    
    spec_hash = latest_run.spec_hash if latest_run else None
    config_fingerprint = latest_run.config_fingerprint if latest_run else None
    provider = None
    model = None
    pipeline_run_id = latest_run.run_id if latest_run else None
    
    # Try to get provider/model from latest stage run
    if latest_run:
        stage_run = CSCLPipelineStageRun.query.filter_by(run_id=latest_run.run_id).first()
        if stage_run:
            provider = stage_run.provider
            model = stage_run.model
    
    summary = DecisionSummaryService.compute_summary(
        script_id=script_id,
        spec_hash=spec_hash,
        config_fingerprint=config_fingerprint,
        provider=provider,
        model=model,
        pipeline_run_id=pipeline_run_id
    )
    
    return jsonify({
        'success': True,
        'summary': summary
    }), 200


@cscl_bp.route('/scripts/<script_id>/decision-timeline/export', methods=['GET'])
@role_required('teacher', 'admin')
def export_decision_timeline(script_id):
    """Export decision timeline for research (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    # Get filter parameters
    decision_type = request.args.get('decision_type')
    target_type = request.args.get('target_type')
    source_stage = request.args.get('source_stage')
    actor_id = request.args.get('actor_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    # Parse time filters
    start_dt = None
    end_dt = None
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'error': 'Invalid start_time format',
                'code': 'INVALID_TIME_FORMAT'
            }), 400
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'error': 'Invalid end_time format',
                'code': 'INVALID_TIME_FORMAT'
            }), 400
    
    # Get timeline
    timeline = DecisionSummaryService.get_timeline(
        script_id=script_id,
        decision_type=decision_type,
        target_type=target_type,
        source_stage=source_stage,
        actor_id=actor_id,
        start_time=start_dt,
        end_time=end_dt
    )
    
    # Get summary
    latest_run = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
        CSCLPipelineRun.created_at.desc()
    ).first()
    
    spec_hash = latest_run.spec_hash if latest_run else None
    config_fingerprint = latest_run.config_fingerprint if latest_run else None
    provider = None
    model = None
    pipeline_run_id = latest_run.run_id if latest_run else None
    
    if latest_run:
        stage_run = CSCLPipelineStageRun.query.filter_by(run_id=latest_run.run_id).first()
        if stage_run:
            provider = stage_run.provider
            model = stage_run.model
    
    summary = DecisionSummaryService.compute_summary(
        script_id=script_id,
        spec_hash=spec_hash,
        config_fingerprint=config_fingerprint,
        provider=provider,
        model=model,
        pipeline_run_id=pipeline_run_id
    )
    
    # Get spec_hash and config_fingerprint from latest pipeline run
    latest_run = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
        CSCLPipelineRun.created_at.desc()
    ).first()
    
    spec_hash = latest_run.spec_hash if latest_run else None
    config_fingerprint = latest_run.config_fingerprint if latest_run else None
    
    # Ensure stable field order for reproducibility
    export_data = {
        'schema_version': '1.0.0',
        'generated_at': datetime.now().isoformat(),
        'script_id': script_id,
        'spec_hash': spec_hash,
        'config_fingerprint': config_fingerprint,
        'timeline': timeline,
        'summary': summary
    }
    
    return jsonify({
        'success': True,
        'export': export_data
    }), 200


@cscl_bp.route('/scripts/<script_id>/revisions/<revision_id>/decisions', methods=['GET'])
@role_required('teacher', 'admin')
def get_revision_decisions(script_id, revision_id):
    """Get decisions associated with a revision (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    revision = CSCLScriptRevision.query.filter_by(id=revision_id, script_id=script_id).first()
    if not revision:
        return jsonify({'error': 'Revision not found'}), 404
    
    decisions = CSCLTeacherDecision.query.filter_by(
        script_id=script_id,
        revision_id=revision_id
    ).order_by(CSCLTeacherDecision.created_at).all()
    
    return jsonify({
        'success': True,
        'revision': revision.to_dict(),
        'decisions': [d.to_dict() for d in decisions],
        'count': len(decisions)
    }), 200


@cscl_bp.route('/scripts/<script_id>/quality-report', methods=['GET'])
@role_required('teacher', 'admin')
def get_quality_report(script_id):
    """Get quality report for a script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({
            'error': 'Script not found',
            'code': 'SCRIPT_NOT_FOUND'
        }), 404
    
    try:
        report = QualityReportService.generate_report(script_id)
        return jsonify({
            'success': True,
            'report': report
        }), 200
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'SCRIPT_NOT_FOUND'
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error generating quality report: {e}")
        return jsonify({
            'error': 'Failed to generate quality report',
            'code': 'REPORT_GENERATION_FAILED'
        }), 500


@cscl_bp.route('/scripts/<script_id>/pipeline/preflight', methods=['POST'])
@role_required('teacher', 'admin')
def pipeline_preflight(script_id):
    """B2: Preflight checks before pipeline run. Returns actionable errors."""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({
            'success': False,
            'ready': False,
            'error_code': 'SCRIPT_NOT_FOUND',
            'message': 'Script not found or access denied.',
            'details': {'script_id': script_id}
        }), 404

    data = request.get_json() or {}
    spec = data.get('spec')
    checks = {'spec_valid': False, 'script_owner': True, 'course_id': None, 'has_docs': False, 'provider_ready': False}

    if not spec:
        return jsonify({
            'success': False,
            'ready': False,
            'error_code': 'MISSING_SPEC',
            'message': 'spec is required in request body.',
            'details': {'checks': checks}
        }), 400

    validation_result = SpecValidator.validate(spec)
    if not validation_result['valid']:
        field_paths = validation_result.get('field_paths') or []
        issues_list = validation_result.get('issues') or []
        issues_structured = [{'field': fp, 'reason': msg} for fp, msg in zip(field_paths, issues_list)]
        if not issues_structured and issues_list:
            issues_structured = [{'field': 'spec', 'reason': '; '.join(issues_list)}]
        return jsonify({
            'success': False,
            'ready': False,
            'error_code': 'SPEC_INVALID',
            'message': 'Spec validation failed. Fix the fields and try again.',
            'details': {'checks': checks, 'issues': issues_structured}
        }), 422

    checks['spec_valid'] = True
    course_id = script.course_id or (validation_result.get('normalized_spec') or {}).get('course_context', {}).get('course_id')
    checks['course_id'] = course_id or ''

    has_docs = False
    if course_id:
        has_docs = CSCLCourseDocument.query.filter_by(course_id=course_id).first() is not None
    checks['has_docs'] = has_docs

    provider_status = select_runnable_provider()
    checks['provider_ready'] = provider_status['ready']

    if not provider_status['ready']:
        return jsonify({
            'success': False,
            'ready': False,
            'error_code': 'LLM_PROVIDER_NOT_READY',
            'message': provider_status.get('reason', 'LLM provider is not ready.'),
            'details': {
                'checks': checks,
                'primary': provider_status.get('primary'),
                'fallback': provider_status.get('fallback'),
                'provider_checks': provider_status.get('checks', {})
            }
        }), 503

    return jsonify({
        'success': True,
        'ready': True,
        'message': 'Preflight passed. You can run the pipeline.',
        'details': {
            'checks': checks,
            'provider': provider_status.get('provider'),
            'grounding_available': has_docs
        }
    }), 200


@cscl_bp.route('/scripts/<script_id>/pipeline/run', methods=['POST'])
@role_required('teacher', 'admin')
def run_pipeline(script_id):
    """Run multi-stage generation pipeline (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    data = request.get_json() or {}
    spec = data.get('spec')
    options = data.get('generation_options', {})
    
    if not spec:
        return jsonify({
            'error': 'spec is required',
            'code': 'MISSING_SPEC'
        }), 400
    
    # Validate spec first
    from app.services.spec_validator import SpecValidator
    validation_result = SpecValidator.validate(spec)
    if not validation_result['valid']:
        field_paths = validation_result.get('field_paths') or []
        issues_list = validation_result.get('issues') or []
        issues_structured = [
            {'field': fp, 'reason': 'required' if 'required' in msg.lower() else 'invalid'}
            for fp, msg in zip(field_paths, issues_list)
        ]
        if not issues_structured and issues_list:
            issues_structured = [{'field': 'spec', 'reason': 'invalid'}]
        return jsonify({
            'error': 'SPEC_INVALID',
            'code': 'SPEC_INVALID',
            'issues': issues_structured,
            'message': 'Spec validation failed.'
        }), 422
    
    # Use normalized spec
    normalized_spec = validation_result['normalized_spec']
    
    # B2: Preflight – do not start run if course_id, docs, or provider checks fail
    course_id = script.course_id or (normalized_spec.get('course_context') or {}).get('course_id') or ''
    if not course_id:
        return jsonify({
            'error': 'Course ID is required for pipeline run. Set course in spec or script.',
            'code': 'PREFLIGHT_MISSING_COURSE_ID',
            'details': {'course_id': ''}
        }), 400
    has_docs = CSCLCourseDocument.query.filter_by(course_id=course_id).first() is not None
    if not has_docs:
        return jsonify({
            'error': 'No course documents for this course. Upload documents in Course Documents first.',
            'code': 'PREFLIGHT_NO_COURSE_DOCS',
            'details': {'course_id': course_id}
        }), 400
    provider_status = select_runnable_provider()
    if not provider_status.get('ready'):
        return jsonify({
            'error': provider_status.get('reason', 'LLM provider is not ready.'),
            'code': 'LLM_PROVIDER_NOT_READY',
            'details': {
                'primary': provider_status.get('primary'),
                'fallback': provider_status.get('fallback'),
                'provider_checks': provider_status.get('checks', {})
            }
        }), 503

    # M5: Idempotency - same Idempotency-Key within window returns existing run
    idem_key = request.headers.get('Idempotency-Key') or (data.get('idempotency_key') if isinstance(data, dict) else None)
    if idem_key:
        from app.services.pipeline.idempotency import get_cached_run_for_key, set_cached_run_for_key
        cached_run_id = get_cached_run_for_key(script_id, idem_key)
        if cached_run_id:
            existing = CSCLPipelineRun.query.filter_by(run_id=cached_run_id).first()
            if existing and existing.script_id == script_id:
                stage_runs = CSCLPipelineStageRun.query.filter_by(run_id=existing.run_id).order_by(CSCLPipelineStageRun.created_at).all()
                return jsonify({
                    'success': True,
                    'run_id': existing.run_id,
                    'status': existing.status,
                    'final_output': None,
                    'quality_report': None,
                    'grounding_status': 'no_course_docs',
                    'stages': [s.to_dict() for s in stage_runs],
                    'idempotent_reuse': True
                }), 200

    # S2.18: Extract force_provider from options for retry scenarios
    force_provider = options.get('force_provider')
    
    # Run pipeline asynchronously so the HTTP request returns immediately
    import threading
    from app import create_app as _create_app

    pipeline_service = CSCLPipelineService(force_provider=force_provider)

    # Pre-create a run_id and return it immediately; pipeline executes in background thread
    import uuid as _uuid
    bg_run_id = f"run_{_uuid.uuid4().hex[:16]}"
    _app = current_app._get_current_object()
    _user_id = current_user.id
    _spec_copy = dict(normalized_spec)
    _options_copy = dict(options) if options else {}
    _idem_key = idem_key
    _script_id = script_id

    def _run_bg():
        with _app.app_context():
            try:
                svc = CSCLPipelineService(force_provider=force_provider)
                svc.run_pipeline(
                    script_id=_script_id,
                    spec=_spec_copy,
                    initiated_by=_user_id,
                    options=_options_copy,
                    run_id_override=bg_run_id,
                )
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Background pipeline failed")

    t = threading.Thread(target=_run_bg, daemon=True)
    t.start()

    return jsonify({
        'success': True,
        'run_id': bg_run_id,
        'status': 'running',
        'async': True,
        'stages': [],
        'final_output': None,
        'quality_report': None,
        'grounding_status': 'pending',
    }), 202


@cscl_bp.route('/pipeline/runs/<run_id>', methods=['GET'])
@role_required('teacher', 'admin')
def get_pipeline_run(run_id):
    """Get pipeline run details (teacher/admin only)"""
    pipeline_run = CSCLPipelineRun.query.filter_by(run_id=run_id).first()
    if not pipeline_run:
        return jsonify({'error': 'Pipeline run not found'}), 404
    
    # Check ownership
    script = CSCLScript.query.get(pipeline_run.script_id)
    if not script or script.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get stage runs
    stage_runs = CSCLPipelineStageRun.query.filter_by(run_id=run_id).order_by(
        CSCLPipelineStageRun.created_at
    ).all()
    
    return jsonify({
        'success': True,
        'run': pipeline_run.to_dict(),
        'stages': [s.to_dict() for s in stage_runs]
    }), 200


@cscl_bp.route('/scripts/<script_id>/pipeline/runs', methods=['GET'])
@role_required('teacher', 'admin')
def get_script_pipeline_runs(script_id):
    """Get pipeline runs for a script (teacher/admin only)"""
    script = CSCLScript.query.filter_by(id=script_id, created_by=current_user.id).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    runs = CSCLPipelineRun.query.filter_by(script_id=script_id).order_by(
        CSCLPipelineRun.created_at.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'runs': [r.to_dict() for r in runs]
    }), 200


# ────────────────────────────────────────────────────────────────
# Course Folder endpoints
# ────────────────────────────────────────────────────────────────

@cscl_bp.route('/folders', methods=['GET'])
@role_required('teacher', 'admin')
def list_folders():
    """List course folders for the current teacher"""
    folders = CSCLCourseFolder.query.filter_by(
        created_by=current_user.id
    ).order_by(CSCLCourseFolder.updated_at.desc()).all()
    return jsonify({
        'success': True,
        'folders': [f.to_dict(include_activity_count=True) for f in folders]
    }), 200


@cscl_bp.route('/folders', methods=['POST'])
@role_required('teacher', 'admin')
def create_folder():
    """Create a new course folder"""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Folder name is required'}), 400

    folder = CSCLCourseFolder(
        name=name,
        description=(data.get('description') or '').strip() or None,
        created_by=current_user.id,
    )
    db.session.add(folder)
    db.session.commit()
    log_audit('course_folder_created', target_id=folder.id)
    return jsonify({'success': True, 'folder': folder.to_dict()}), 201


@cscl_bp.route('/folders/<folder_id>', methods=['GET'])
@role_required('teacher', 'admin')
def get_folder(folder_id):
    """Get a course folder with its activities"""
    folder = CSCLCourseFolder.query.filter_by(
        id=folder_id, created_by=current_user.id
    ).first()
    if not folder:
        return jsonify({'error': 'Folder not found'}), 404

    activities = CSCLScript.query.filter_by(folder_id=folder_id).order_by(
        CSCLScript.updated_at.desc()
    ).all()
    docs = CSCLCourseDocument.query.filter_by(course_id=folder_id).all()
    return jsonify({
        'success': True,
        'folder': folder.to_dict(),
        'activities': [a.to_dict() for a in activities],
        'documents': [d.to_dict() for d in docs],
    }), 200


@cscl_bp.route('/folders/<folder_id>', methods=['PUT'])
@role_required('teacher', 'admin')
def update_folder(folder_id):
    """Update a course folder"""
    folder = CSCLCourseFolder.query.filter_by(
        id=folder_id, created_by=current_user.id
    ).first()
    if not folder:
        return jsonify({'error': 'Folder not found'}), 404

    data = request.get_json() or {}
    if 'name' in data:
        name = (data['name'] or '').strip()
        if not name:
            return jsonify({'error': 'Folder name cannot be empty'}), 400
        folder.name = name
    if 'description' in data:
        folder.description = (data['description'] or '').strip() or None

    db.session.commit()
    return jsonify({'success': True, 'folder': folder.to_dict()}), 200


@cscl_bp.route('/folders/<folder_id>', methods=['DELETE'])
@role_required('teacher', 'admin')
def delete_folder(folder_id):
    """Delete a course folder (only if no activities)"""
    folder = CSCLCourseFolder.query.filter_by(
        id=folder_id, created_by=current_user.id
    ).first()
    if not folder:
        return jsonify({'error': 'Folder not found'}), 404

    if folder.activities.count() > 0:
        return jsonify({'error': 'Cannot delete folder with existing activities'}), 400

    db.session.delete(folder)
    db.session.commit()
    log_audit('course_folder_deleted', target_id=folder_id)
    return jsonify({'success': True}), 200
