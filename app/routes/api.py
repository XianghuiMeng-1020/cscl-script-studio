"""API routes blueprint"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid
import re
from app.config import Config
from app.db import check_db_connection, db
from app.services.cscl_llm_provider import get_llm_provider_status
from app.utils import (
    load_json, save_json, log_activity, get_system_config,
    analyze_student_work, analyze_feedback_detailed, track_engagement
)
from app.repositories import get_assignment_repo, get_submission_repo, get_rubric_repo, get_user_repo
from app.auth import role_required, student_resource_required, login_required, log_audit
from flask_login import current_user
from app.ai_services import (
    ai_check_rubric_alignment, ai_analyze_feedback_quality,
    ai_improve_feedback, ai_generate_visual_summary, ai_generate_video_script,
    call_llm_api
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== Health Check API ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - returns system status. S2.18: includes LLM provider readiness."""
    db_configured = bool(current_app.config.get('DATABASE_URL', ''))
    db_connected = False
    
    if db_configured:
        try:
            db_connected = check_db_connection(current_app)
        except Exception:
            db_connected = False
    
    # S2.18: Get LLM provider readiness status using unified selection logic
    llm_status = get_llm_provider_status()
    
    return jsonify({
        "status": "ok",
        "db_configured": db_configured,
        "db_connected": db_connected,
        "use_db_storage": Config.USE_DB_STORAGE,
        "provider": Config.LLM_PROVIDER,
        "auth_mode": "session+token",
        "rbac_enabled": True,
        "llm_primary": llm_status.get('llm_primary', Config.LLM_PROVIDER_PRIMARY),
        "llm_fallback": llm_status.get('llm_fallback', Config.LLM_PROVIDER_FALLBACK),
        "llm_strategy": llm_status.get('llm_strategy', Config.LLM_STRATEGY),
        "llm_provider_ready": llm_status['llm_provider_ready'],
        "llm_provider_name": llm_status['llm_provider_name'],
        "llm_provider_reason": llm_status['llm_provider_reason']
    }), 200


# ==================== Assignment APIs ====================

@api_bp.route('/assignments', methods=['GET'])
def get_assignments():
    """Get all assignments"""
    assignments = load_json(Config.ASSIGNMENTS_FILE)
    return jsonify(assignments), 200


@api_bp.route('/assignments', methods=['POST'])
@role_required('teacher', 'admin')
def create_assignment():
    """Create new assignment (teacher/admin only)"""
    data = request.get_json()
    assignments = load_json(Config.ASSIGNMENTS_FILE)
    
    assignment = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'course_id': data.get('course_id', ''),
        'due_date': data.get('due_date', ''),
        'rubric_id': data.get('rubric_id', ''),
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    assignments.append(assignment)
    save_json(Config.ASSIGNMENTS_FILE, assignments)
    
    log_audit(
        'create_assignment',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=assignment['id'],
        status='success'
    )
    
    return jsonify({'message': 'Assignment created successfully', 'assignment': assignment}), 201


# ==================== Rubric APIs ====================

@api_bp.route('/rubrics', methods=['GET'])
def get_rubrics():
    """Get all rubrics"""
    rubrics = load_json(Config.RUBRICS_FILE)
    return jsonify(rubrics), 200


@api_bp.route('/rubrics', methods=['POST'])
@role_required('teacher', 'admin')
def create_rubric():
    """Create new rubric (teacher/admin only)"""
    data = request.get_json()
    rubrics = load_json(Config.RUBRICS_FILE)
    
    rubric = {
        'id': str(uuid.uuid4())[:8],
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'criteria': data.get('criteria', []),
        'created_at': datetime.now().isoformat()
    }
    
    rubrics.append(rubric)
    save_json(Config.RUBRICS_FILE, rubrics)
    
    log_audit(
        'create_rubric',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=rubric['id'],
        status='success'
    )
    
    return jsonify({'message': 'Rubric created successfully', 'rubric': rubric}), 201


# ==================== Submission APIs ====================

@api_bp.route('/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions with optional filtering"""
    submission_repo = get_submission_repo()
    
    assignment_id = request.args.get('assignment_id')
    student_id = request.args.get('student_id')
    status = request.args.get('status')
    
    submissions = submission_repo.get_all(
        assignment_id=assignment_id,
        student_id=student_id,
        status=status
    )
    
    return jsonify(submissions), 200


@api_bp.route('/submissions', methods=['POST'])
@login_required
def create_submission():
    """Create new submission (student submits work)"""
    data = request.get_json()
    
    # Students can only submit for themselves
    student_id = data.get('student_id', '')
    if current_user.role.value == 'student' and student_id != current_user.id:
        return jsonify({'error': 'Students can only submit for themselves'}), 403
    
    submissions = load_json(Config.SUBMISSIONS_FILE)
    
    submission = {
        'id': str(uuid.uuid4())[:8],
        'assignment_id': data.get('assignment_id', ''),
        'student_id': student_id or current_user.id,
        'student_name': data.get('student_name', ''),
        'content': data.get('content', ''),
        'submitted_at': datetime.now().isoformat(),
        'status': 'pending',
        'feedback': None,
        'rubric_scores': None,
        'visual_summary': None,
        'video_script': None,
        'feedback_quality': None,
        'graded_at': None
    }
    
    submissions.append(submission)
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    log_audit(
        'submit_assignment',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=submission['id'],
        status='success'
    )
    
    return jsonify({'message': 'Submission created successfully', 'submission': submission}), 201


@api_bp.route('/submissions/<submission_id>', methods=['GET'])
@student_resource_required
def get_submission(submission_id):
    """Get specific submission"""
    submissions = load_json(Config.SUBMISSIONS_FILE)
    submission = next((s for s in submissions if s['id'] == submission_id), None)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    # Additional check for students
    if current_user.role.value == 'student' and submission.get('student_id') != current_user.id:
        return jsonify({'error': 'Access denied: cannot access other students\' resources'}), 403
    
    return jsonify(submission), 200


@api_bp.route('/submissions/<submission_id>/feedback', methods=['PUT'])
@role_required('teacher', 'admin')
def update_submission_feedback(submission_id):
    """Update submission with feedback (teacher/admin only)"""
    data = request.get_json()
    submissions = load_json(Config.SUBMISSIONS_FILE)
    
    submission = next((s for s in submissions if s['id'] == submission_id), None)
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    # Update feedback
    submission['feedback'] = data.get('feedback', '')
    submission['rubric_scores'] = data.get('rubric_scores', {})
    submission['status'] = 'graded'
    submission['graded_at'] = datetime.now().isoformat()
    
    # Generate visual summary and video script if feedback is provided
    if submission['feedback']:
        visual_summary = ai_generate_visual_summary(
            submission['feedback'], 
            submission['rubric_scores']
        )
        if not visual_summary.get('error'):
            submission['visual_summary'] = visual_summary
        
        video_script_result = ai_generate_video_script(
            submission['feedback'],
            submission['rubric_scores'],
            submission['student_name']
        )
        if not video_script_result.get('error'):
            submission['video_script'] = video_script_result.get('script', '')
    
    save_json(Config.SUBMISSIONS_FILE, submissions)
    
    log_audit(
        'submit_feedback',
        actor_id=current_user.id,
        role=current_user.role,
        target_id=submission_id,
        status='success'
    )
    
    return jsonify({'message': 'Feedback saved successfully', 'submission': submission}), 200


# ==================== AI Analysis APIs ====================

@api_bp.route('/ai/check-alignment', methods=['POST'])
def check_alignment():
    """Check feedback alignment with rubric"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    result = ai_check_rubric_alignment(feedback, rubric_criteria)
    
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(result), 200


@api_bp.route('/ai/analyze-quality', methods=['POST'])
def analyze_quality():
    """Analyze feedback quality"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    
    result = ai_analyze_feedback_quality(feedback)
    
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(result), 200


@api_bp.route('/ai/improve-feedback', methods=['POST'])
def improve_feedback():
    """Get AI suggestions to improve feedback"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    improvement_type = data.get('type', 'comprehensive')
    rubric_criteria = data.get('rubric_criteria', None)
    student_work = data.get('student_work', None)
    
    result = ai_improve_feedback(feedback, improvement_type, rubric_criteria, student_work)
    
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured",
            "improved_feedback": ""
        }), 503
    
    return jsonify(result), 200


@api_bp.route('/ai/generate-summary', methods=['POST'])
def generate_summary():
    """Generate visual summary for student"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_scores = data.get('rubric_scores', {})
    
    summary = ai_generate_visual_summary(feedback, rubric_scores)
    
    if summary.get('error'):
        return jsonify({
            "error": summary['error'],
            "provider": summary.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(summary), 200


@api_bp.route('/ai/generate-script', methods=['POST'])
def generate_script():
    """Generate video feedback script"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_scores = data.get('rubric_scores', {})
    student_name = data.get('student_name', 'Student')
    
    result = ai_generate_video_script(feedback, rubric_scores, student_name)
    
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured",
            "script": ""
        }), 503
    
    return jsonify(result), 200


@api_bp.route('/ai/analyze-work', methods=['POST'])
def analyze_work():
    """Analyze student work structure and content"""
    data = request.get_json()
    content = data.get('content', '')
    
    analysis = analyze_student_work(content)
    
    log_activity("work_analysis", data.get('teacher_id', 'unknown'), {
        "submission_id": data.get('submission_id'),
        "word_count": analysis['word_count']
    })
    
    return jsonify(analysis), 200


@api_bp.route('/ai/suggest-scores', methods=['POST'])
def suggest_scores():
    """AI suggests rubric scores based on student work"""
    data = request.get_json()
    student_work = data.get('student_work', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    # Import here to avoid circular dependency
    from app.utils import analyze_student_work
    work_analysis = analyze_student_work(student_work)
    
    criteria_list = "\n".join([
        f"- {c['name']} ({c.get('weight', 0)}%): {c['description']} [Levels: {', '.join(c.get('levels', []))}]" 
        for c in rubric_criteria
    ])
    
    prompt = f"""Based on the student work analysis and rubric criteria, suggest appropriate scores.

Student Work:
"{student_work[:2000]}"

Work Analysis:
- Word count: {work_analysis['word_count']}
- Structure: Title={work_analysis['structure']['has_title']}, Intro={work_analysis['structure']['has_introduction']}, Conclusion={work_analysis['structure']['has_conclusion']}
- Lexical diversity: {work_analysis['lexical_diversity']}

Rubric Criteria:
{criteria_list}

For each criterion, suggest a performance level and provide a brief rationale (for instructor reference only).

Return in JSON format:
{{
    "suggestions": [
        {{
            "criterion_id": "C1",
            "criterion_name": "criterion name",
            "suggested_level": "one of the performance levels",
            "confidence": 0.0-1.0,
            "rationale": "brief explanation for instructor"
        }}
    ],
    "overall_assessment": "brief overall assessment"
}}

Return only JSON."""
    
    system_message = "You are an educational assessment expert. Provide fair, evidence-based scoring suggestions."
    llm_response = call_llm_api(prompt, system_message, max_tokens=800)
    
    if llm_response.get('error'):
        suggestions = []
        for c in rubric_criteria:
            level_idx = 1 if work_analysis['quality_indicators']['length_adequate'] else 2
            suggestions.append({
                "criterion_id": c['id'],
                "criterion_name": c['name'],
                "suggested_level": c.get('levels', ['Good', 'Fair'])[min(level_idx, len(c.get('levels', []))-1)],
                "confidence": 0.5,
                "rationale": "Based on automated text analysis"
            })
        
        return jsonify({
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "suggestions": suggestions,
            "overall_assessment": f"LLM error: {llm_response['error']}"
        }), 503
    
    result_text = llm_response.get('content', '')
    try:
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            import json
            parsed = json.loads(json_match.group())
            parsed['provider'] = llm_response['provider']
            parsed['model'] = llm_response['model']
            if llm_response.get('warnings'):
                parsed['warnings'] = llm_response['warnings']
            
            log_activity("score_suggestion", data.get('teacher_id', 'unknown'), {
                "submission_id": data.get('submission_id'),
                "suggestions_count": len(parsed.get('suggestions', []))
            })
            
            return jsonify(parsed), 200
    except:
        pass
    
    # Fallback
    suggestions = []
    for c in rubric_criteria:
        level_idx = 1 if work_analysis['quality_indicators']['length_adequate'] else 2
        suggestions.append({
            "criterion_id": c['id'],
            "criterion_name": c['name'],
            "suggested_level": c.get('levels', ['Good', 'Fair'])[min(level_idx, len(c.get('levels', []))-1)],
            "confidence": 0.5,
            "rationale": "Based on automated text analysis"
        })
    
    return jsonify({
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "suggestions": suggestions,
        "overall_assessment": "Automated analysis - please review carefully",
        "warnings": llm_response.get('warnings', [])
    }), 200


@api_bp.route('/ai/detailed-analysis', methods=['POST'])
def detailed_analysis():
    """Comprehensive feedback analysis with coverage details"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    student_work = data.get('student_work', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    analysis = analyze_feedback_detailed(feedback, student_work, rubric_criteria)
    
    log_activity("detailed_analysis", data.get('teacher_id', 'unknown'), {
        "submission_id": data.get('submission_id'),
        "overall_coverage": analysis['overall_coverage'],
        "flags": analysis['flags']
    })
    
    return jsonify(analysis), 200


# ==================== Engagement Tracking APIs ====================

@api_bp.route('/engagement/track', methods=['POST'])
def track_student_engagement():
    """Track student engagement with feedback"""
    data = request.get_json()
    student_id = data.get('student_id', '')
    submission_id = data.get('submission_id', '')
    action = data.get('action', '')
    details = data.get('details', {})
    
    record = track_engagement(student_id, submission_id, action, details)
    return jsonify(record), 200


@api_bp.route('/engagement/stats', methods=['GET'])
def get_engagement_stats():
    """Get engagement statistics"""
    engagement = load_json(Config.ENGAGEMENT_FILE)
    if not isinstance(engagement, dict):
        engagement = {}
    
    total_views = sum(r.get('view_count', 0) for r in engagement.values())
    visual_views = sum(r.get('visual_summary_views', 0) for r in engagement.values())
    script_views = sum(r.get('video_script_views', 0) for r in engagement.values())
    
    stats = {
        "total_feedback_views": total_views,
        "visual_summary_views": visual_views,
        "video_script_views": script_views,
        "unique_students": len(set(r.get('student_id') for r in engagement.values())),
        "avg_views_per_feedback": round(total_views / max(len(engagement), 1), 2)
    }
    
    return jsonify(stats), 200


# ==================== Logging APIs ====================

@api_bp.route('/logs', methods=['GET'])
def get_activity_logs():
    """Get activity logs with optional filtering"""
    logs = load_json(Config.LOGS_FILE)
    
    log_type = request.args.get('type')
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 100, type=int)
    
    if log_type:
        logs = [l for l in logs if l.get('type') == log_type]
    if user_id:
        logs = [l for l in logs if l.get('user_id') == user_id]
    
    logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    return jsonify(logs), 200


@api_bp.route('/logs/summary', methods=['GET'])
def get_logs_summary():
    """Get summary of activity logs"""
    logs = load_json(Config.LOGS_FILE)
    
    summary = {
        "total_activities": len(logs),
        "by_type": {},
        "suggestions_accepted": 0,
        "suggestions_ignored": 0,
        "avg_grading_time_seconds": 0
    }
    
    grading_times = []
    for log in logs:
        log_type = log.get('type', 'unknown')
        summary['by_type'][log_type] = summary['by_type'].get(log_type, 0) + 1
        
        if log_type == 'suggestion_accepted':
            summary['suggestions_accepted'] += 1
        elif log_type == 'suggestion_ignored':
            summary['suggestions_ignored'] += 1
        elif log_type == 'grading_completed':
            if 'grading_time' in log.get('details', {}):
                grading_times.append(log['details']['grading_time'])
    
    if grading_times:
        summary['avg_grading_time_seconds'] = round(sum(grading_times) / len(grading_times), 1)
    
    return jsonify(summary), 200


# ==================== Configuration APIs ====================

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get system configuration"""
    config = get_system_config()
    return jsonify(config), 200


@api_bp.route('/config', methods=['PUT'])
def update_config():
    """Update system configuration"""
    data = request.get_json()
    config = get_system_config()
    
    if 'features' in data:
        config['features'].update(data['features'])
    if 'thresholds' in data:
        config['thresholds'].update(data['thresholds'])
    if 'limits' in data:
        config['limits'].update(data['limits'])
    
    save_json(Config.CONFIG_FILE, config)
    
    log_activity("config_updated", "admin", {"changes": data})
    
    return jsonify({'message': 'Configuration updated', 'config': config}), 200


# ==================== Statistics APIs ====================

@api_bp.route('/stats/teacher', methods=['GET'])
def get_teacher_stats():
    """Get teacher dashboard statistics"""
    assignment_repo = get_assignment_repo()
    submission_repo = get_submission_repo()
    
    assignments = assignment_repo.get_all()
    submissions = submission_repo.get_all()
    
    stats = {
        'total_assignments': len(assignments),
        'total_submissions': len(submissions),
        'pending_grading': len([s for s in submissions if s.get('status') == 'pending']),
        'graded': len([s for s in submissions if s.get('status') == 'graded']),
        'average_score': 0
    }
    
    # Note: rubric_scores are stored in Feedback model, not Submission
    # For now, we'll calculate average_score as 0 (can be enhanced later)
    
    return jsonify(stats), 200


@api_bp.route('/stats/student/<student_id>', methods=['GET'])
@student_resource_required
def get_student_stats(student_id):
    """Get student statistics"""
    # Additional check: students can only view their own stats
    if current_user.role.value == 'student' and student_id != current_user.id:
        return jsonify({'error': 'Access denied: cannot access other students\' resources'}), 403
    
    submission_repo = get_submission_repo()
    student_submissions = submission_repo.get_all(student_id=student_id)
    
    stats = {
        'total_submissions': len(student_submissions),
        'graded': len([s for s in student_submissions if s.get('status') == 'graded']),
        'pending': len([s for s in student_submissions if s.get('status') == 'pending']),
        'submissions': student_submissions
    }
    
    return jsonify(stats), 200


# ==================== User APIs ====================

@api_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = load_json(Config.USERS_FILE)
    return jsonify(users), 200


# ==================== Demo Data ====================

@api_bp.route('/demo/init', methods=['POST'])
def init_demo_data():
    """Initialize demo data for testing (idempotent: clears existing data first)"""
    actor_id = current_user.id if current_user.is_authenticated else None
    role = current_user.role if current_user.is_authenticated else None
    
    try:
        # Get repositories
        user_repo = get_user_repo()
        rubric_repo = get_rubric_repo()
        assignment_repo = get_assignment_repo()
        submission_repo = get_submission_repo()
        
        # Clear existing data for idempotency
        submission_repo.delete_all()  # Delete submissions first (due to foreign keys)
        assignment_repo.delete_all()
        rubric_repo.delete_all()
        if Config.USE_DB_STORAGE:
            user_repo.delete_all()  # Only delete users in DB mode
        
        # Create demo users (required for foreign key constraints in DB mode)
        if Config.USE_DB_STORAGE:
            user_repo.create({
                'id': 'S001',
                'role': 'student',
                'created_at': datetime.now().isoformat()
            })
            user_repo.create({
                'id': 'S002',
                'role': 'student',
                'created_at': datetime.now().isoformat()
            })
        
        # Create sample rubric
        rubric_data = {
            'id': 'R001',
            'name': 'Essay Writing Rubric',
            'description': 'Comprehensive rubric for evaluating academic essays',
            'criteria': [
                {'id': 'C1', 'name': 'Argument Clarity', 'description': 'Is the thesis clear and the argument well-defined?', 'weight': 25, 'levels': ['Excellent', 'Good', 'Fair', 'Needs Improvement']},
                {'id': 'C2', 'name': 'Evidence Support', 'description': 'Are there sufficient evidence and examples to support the argument?', 'weight': 25, 'levels': ['Excellent', 'Good', 'Fair', 'Needs Improvement']},
                {'id': 'C3', 'name': 'Organization', 'description': 'Is the structure clear with smooth paragraph transitions?', 'weight': 25, 'levels': ['Excellent', 'Good', 'Fair', 'Needs Improvement']},
                {'id': 'C4', 'name': 'Language Expression', 'description': 'Is the language accurate, fluent, and grammatically correct?', 'weight': 25, 'levels': ['Excellent', 'Good', 'Fair', 'Needs Improvement']}
            ],
            'created_at': datetime.now().isoformat()
        }
        rubric_repo.create(rubric_data)
        
        # Create sample assignment
        assignment_data = {
            'id': 'A001',
            'title': 'AI Ethics Analysis Essay',
            'description': 'Write a 1500-word essay analyzing ethical issues in AI development and provide your perspectives and recommendations.',
            'course_id': 'CS101',
            'due_date': '2025-12-20',
            'rubric_id': 'R001',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        assignment_repo.create(assignment_data)
        
        # Create sample submissions
        submission1_data = {
            'id': 'SUB001',
            'assignment_id': 'A001',
            'student_id': 'S001',
            'student_name': 'John Smith',
            'content': '''Analysis of Ethical Issues in Artificial Intelligence

With the rapid development of artificial intelligence technology, we face increasing ethical challenges. This essay will analyze three key areas: privacy protection, employment impact, and algorithmic bias.

First, AI systems require large amounts of data for training, which raises serious privacy concerns. Many companies lack transparency when collecting user data, and users often don't know how their data is being used.

Second, automation and the proliferation of AI are changing the job market. While AI creates new job opportunities, it also leads to the disappearance of many traditional positions, posing challenges to social stability.

Finally, AI algorithms may contain biases. If the training data itself contains biases, AI systems will amplify these biases, leading to unfair decisions.

In conclusion, we need to establish a comprehensive AI ethics framework to protect human interests while promoting technological development.''',
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        submission_repo.create(submission1_data)
        
        submission2_data = {
            'id': 'SUB002',
            'assignment_id': 'A001',
            'student_id': 'S002',
            'student_name': 'Emily Johnson',
            'content': '''Thoughts on AI Ethics

Artificial intelligence is important. It has both advantages and disadvantages.

The advantage is that it can help us do many things. The disadvantage is that there might be problems.

I think we should develop AI well, but also pay attention to problems.''',
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        submission_repo.create(submission2_data)
        
        log_audit(
            'demo_init',
            actor_id=actor_id,
            role=role,
            status='success'
        )
        
        return jsonify({'message': 'Demo data initialized successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error initializing demo data: {e}")
        log_audit(
            'demo_init',
            actor_id=actor_id,
            role=role,
            status='failed',
            meta={'error': str(e)}
        )
        return jsonify({'error': str(e)}), 500


@api_bp.route('/demo/scripts', methods=['GET'])
def list_demo_scripts():
    """List scripts for Quick Demo (no auth) - read-only, limit 20."""
    from app.models import CSCLScript
    scripts = CSCLScript.query.order_by(CSCLScript.created_at.desc()).limit(20).all()
    return jsonify({
        'success': True,
        'scripts': [s.to_dict() for s in scripts]
    }), 200
