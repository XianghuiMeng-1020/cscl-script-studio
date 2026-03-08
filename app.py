"""
Application entry point - maintains backward compatibility
For new code, use: from app import create_app; app = create_app()
"""
import os
from app import create_app

# Create app instance
app = create_app()

# Import config for backward compatibility
from app.config import Config
DATA_DIR = Config.DATA_DIR
ASSIGNMENTS_FILE = Config.ASSIGNMENTS_FILE
SUBMISSIONS_FILE = Config.SUBMISSIONS_FILE
RUBRICS_FILE = Config.RUBRICS_FILE
USERS_FILE = Config.USERS_FILE
LOGS_FILE = Config.LOGS_FILE
CONFIG_FILE = Config.CONFIG_FILE
ENGAGEMENT_FILE = Config.ENGAGEMENT_FILE

# System Configuration (Feature Toggles)
DEFAULT_CONFIG = {
    "features": {
        "alignment_check": True,
        "quality_analysis": True,
        "ai_suggestions": True,
        "auto_scoring": True,
        "visual_summary": True,
        "video_script": True
    },
    "thresholds": {
        "coverage_warning": 50,
        "quality_warning": 3,
        "similarity_threshold": 0.5
    },
    "limits": {
        "max_suggestions": 5,
        "script_max_words": 200
    }
}

# LLM Provider initialization (lazy loading)
_llm_provider = None

def get_provider():
    """Get LLM provider instance (singleton)"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider()
    return _llm_provider

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize data files
def init_data_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

# Initialize all data files with sample data
init_data_file(ASSIGNMENTS_FILE, [])
init_data_file(SUBMISSIONS_FILE, [])
init_data_file(RUBRICS_FILE, [])
init_data_file(USERS_FILE, {
    "teachers": [
        {"id": "T001", "name": "Prof. Smith", "email": "smith@university.edu", "courses": ["CS101", "CS201"]}
    ],
    "students": [
        {"id": "S001", "name": "John Smith", "email": "john@student.edu", "courses": ["CS101"]},
        {"id": "S002", "name": "Emily Johnson", "email": "emily@student.edu", "courses": ["CS101"]},
        {"id": "S003", "name": "Michael Brown", "email": "michael@student.edu", "courses": ["CS101"]}
    ]
})
init_data_file(LOGS_FILE, [])
init_data_file(CONFIG_FILE, DEFAULT_CONFIG)
init_data_file(ENGAGEMENT_FILE, {})

# ==================== Logging System ====================
def log_activity(activity_type, user_id, details):
    """Log system activity for analytics"""
    logs = load_json(LOGS_FILE)
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "type": activity_type,
        "user_id": user_id,
        "details": details
    }
    logs.append(log_entry)
    save_json(LOGS_FILE, logs)
    return log_entry

def get_system_config():
    """Get current system configuration"""
    config = load_json(CONFIG_FILE)
    if not config:
        config = DEFAULT_CONFIG
        save_json(CONFIG_FILE, config)
    return config

# ==================== Student Work Analysis Module ====================
def analyze_student_work(content):
    """Analyze student submission structure and content"""
    # Segment the text into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Basic text analysis
    words = content.split()
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Identify structure
    has_title = len(paragraphs) > 0 and len(paragraphs[0].split()) < 15
    has_introduction = len(paragraphs) > 1
    has_conclusion = len(paragraphs) > 2 and any(
        word in paragraphs[-1].lower() 
        for word in ['conclusion', 'summary', 'in conclusion', 'finally', 'therefore']
    )
    
    # Calculate metrics
    avg_sentence_length = len(words) / max(len(sentences), 1)
    avg_paragraph_length = len(words) / max(len(paragraphs), 1)
    
    # Lexical diversity (unique words / total words)
    unique_words = set(word.lower() for word in words if word.isalpha())
    lexical_diversity = len(unique_words) / max(len(words), 1)
    
    # Detect key structural elements
    segments = []
    for i, para in enumerate(paragraphs):
        segment_type = "body"
        if i == 0 and has_title:
            segment_type = "title"
        elif i == 1 or (i == 0 and not has_title):
            segment_type = "introduction"
        elif i == len(paragraphs) - 1 and has_conclusion:
            segment_type = "conclusion"
        
        segments.append({
            "index": i,
            "type": segment_type,
            "text": para[:200] + "..." if len(para) > 200 else para,
            "word_count": len(para.split())
        })
    
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "avg_sentence_length": round(avg_sentence_length, 1),
        "avg_paragraph_length": round(avg_paragraph_length, 1),
        "lexical_diversity": round(lexical_diversity, 3),
        "structure": {
            "has_title": has_title,
            "has_introduction": has_introduction,
            "has_conclusion": has_conclusion
        },
        "segments": segments,
        "quality_indicators": {
            "length_adequate": len(words) >= 300,
            "well_structured": has_introduction and has_conclusion,
            "diverse_vocabulary": lexical_diversity > 0.4
        }
    }

# ==================== Rubric-Aligned Scoring Assistance ====================
def ai_suggest_scores(student_work, rubric_criteria):
    """AI suggests scores based on student work analysis"""
    work_analysis = analyze_student_work(student_work)
    
    criteria_list = "\n".join([
        f"- {c['name']} ({c['weight']}%): {c['description']} [Levels: {', '.join(c['levels'])}]" 
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
    
    # Check for errors
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "suggestions": [],
            "overall_assessment": f"LLM error: {llm_response['error']}"
        }
    
    result_text = llm_response.get('content', '')
    try:
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            parsed = json.loads(json_match.group())
            parsed['provider'] = llm_response['provider']
            parsed['model'] = llm_response['model']
            if llm_response.get('warnings'):
                parsed['warnings'] = llm_response['warnings']
            return parsed
    except:
        pass
    
    # Fallback: generate basic suggestions based on analysis
    suggestions = []
    for c in rubric_criteria:
        level_idx = 1 if work_analysis['quality_indicators']['length_adequate'] else 2
        suggestions.append({
            "criterion_id": c['id'],
            "criterion_name": c['name'],
            "suggested_level": c['levels'][min(level_idx, len(c['levels'])-1)],
            "confidence": 0.5,
            "rationale": "Based on automated text analysis"
        })
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "suggestions": suggestions,
        "overall_assessment": "Automated analysis - please review carefully",
        "warnings": llm_response.get('warnings', [])
    }

# ==================== Enhanced Feedback Analysis ====================
def analyze_feedback_detailed(feedback_text, student_work, rubric_criteria):
    """Comprehensive feedback analysis with semantic matching"""
    
    # Basic keyword extraction for each criterion
    criterion_keywords = {}
    for c in rubric_criteria:
        # Extract keywords from criterion name and description
        words = re.findall(r'\b\w+\b', (c['name'] + ' ' + c['description']).lower())
        criterion_keywords[c['id']] = {
            'name': c['name'],
            'keywords': set(words) - {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'to', 'of', 'in', 'for'}
        }
    
    # Analyze feedback coverage
    feedback_lower = feedback_text.lower()
    feedback_words = set(re.findall(r'\b\w+\b', feedback_lower))
    
    coverage_details = []
    for cid, cdata in criterion_keywords.items():
        # Calculate keyword overlap
        overlap = feedback_words & cdata['keywords']
        coverage_score = len(overlap) / max(len(cdata['keywords']), 1)
        
        coverage_details.append({
            "criterion_id": cid,
            "criterion_name": cdata['name'],
            "coverage_score": round(coverage_score * 100, 1),
            "matched_keywords": list(overlap)[:5],
            "status": "covered" if coverage_score > 0.3 else "potentially_missing"
        })
    
    # Detect feedback quality markers
    specificity_markers = [
        r'paragraph \d+', r'section \d+', r'line \d+', r'page \d+',
        r'your (argument|point|claim|statement|example)',
        r'you (wrote|said|mentioned|stated)',
        r'"[^"]{10,}"'  # Quoted text
    ]
    
    feedforward_markers = [
        r'next time', r'in (the )?future', r'try to', r'consider',
        r'you (could|should|might)', r'improve by', r'suggestion',
        r'recommend', r'for your next'
    ]
    
    tone_positive = ['good', 'great', 'excellent', 'well done', 'strong', 'clear', 'effective']
    tone_negative = ['poor', 'weak', 'unclear', 'confusing', 'wrong', 'bad', 'fail']
    
    specificity_count = sum(1 for pattern in specificity_markers if re.search(pattern, feedback_lower))
    feedforward_count = sum(1 for pattern in feedforward_markers if re.search(pattern, feedback_lower))
    positive_count = sum(1 for word in tone_positive if word in feedback_lower)
    negative_count = sum(1 for word in tone_negative if word in feedback_lower)
    
    return {
        "coverage_details": coverage_details,
        "overall_coverage": round(sum(c['coverage_score'] for c in coverage_details) / max(len(coverage_details), 1), 1),
        "quality_markers": {
            "specificity_indicators": specificity_count,
            "feedforward_indicators": feedforward_count,
            "positive_tone_words": positive_count,
            "negative_tone_words": negative_count,
            "balance_ratio": round(positive_count / max(positive_count + negative_count, 1), 2)
        },
        "flags": {
            "needs_more_specificity": specificity_count < 2,
            "needs_feedforward": feedforward_count < 1,
            "tone_too_negative": negative_count > positive_count * 2
        }
    }

# ==================== Engagement Metrics ====================
def track_engagement(student_id, submission_id, action, details=None):
    """Track student engagement with feedback"""
    engagement = load_json(ENGAGEMENT_FILE)
    
    key = f"{student_id}_{submission_id}"
    if key not in engagement:
        engagement[key] = {
            "student_id": student_id,
            "submission_id": submission_id,
            "first_view": None,
            "view_count": 0,
            "visual_summary_views": 0,
            "video_script_views": 0,
            "time_spent_seconds": 0,
            "actions": []
        }
    
    record = engagement[key]
    timestamp = datetime.now().isoformat()
    
    if action == "view_feedback":
        if not record["first_view"]:
            record["first_view"] = timestamp
        record["view_count"] += 1
    elif action == "view_visual_summary":
        record["visual_summary_views"] += 1
    elif action == "view_video_script":
        record["video_script_views"] += 1
    elif action == "time_spent":
        record["time_spent_seconds"] += details.get("seconds", 0)
    
    record["actions"].append({
        "action": action,
        "timestamp": timestamp,
        "details": details
    })
    
    engagement[key] = record
    save_json(ENGAGEMENT_FILE, engagement)
    return record

# Data loading/saving functions
def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return [] if 'users' not in filepath else {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# AI Helper Functions
def call_llm_api(prompt, system_message="You are a helpful educational assistant.", max_tokens=1000, temperature=0.7):
    """
    统一的LLM API调用入口
    
    返回格式:
    {
        "provider": str,
        "model": str,
        "content": str,
        "warnings": list[str],
        "error": Optional[str]
    }
    """
    provider = get_provider()
    return provider.generate(
        prompt=prompt,
        system_message=system_message,
        max_tokens=max_tokens,
        temperature=temperature
    )

def ai_check_rubric_alignment(feedback_text, rubric_criteria):
    """Check if feedback covers all rubric criteria"""
    criteria_list = "\n".join([f"- {c['name']}: {c['description']}" for c in rubric_criteria])
    
    prompt = f"""Analyze whether the following instructor feedback covers all dimensions in the rubric criteria.

Rubric Criteria:
{criteria_list}

Instructor Feedback:
"{feedback_text}"

Please return the analysis result in JSON format:
{{
    "covered_criteria": ["list of covered criteria names"],
    "missing_criteria": ["list of missing criteria names"],
    "coverage_score": coverage score from 0-100,
    "suggestions": ["list of improvement suggestions"]
}}

Return only JSON, no other content."""
    
    system_message = "You are an educational assessment expert specializing in analyzing the quality and completeness of teaching feedback."
    llm_response = call_llm_api(prompt, system_message)
    
    # Check for errors
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "covered_criteria": [],
            "missing_criteria": [c['name'] for c in rubric_criteria],
            "coverage_score": 0,
            "suggestions": [f"LLM error: {llm_response['error']}"]
        }
    
    result_text = llm_response.get('content', '')
    try:
        # Try to parse JSON directly first (for mock provider which returns clean JSON)
        parsed = json.loads(result_text)
        # Add provider info
        parsed['provider'] = llm_response['provider']
        parsed['model'] = llm_response['model']
        if llm_response.get('warnings'):
            parsed['warnings'] = llm_response['warnings']
        return parsed
    except json.JSONDecodeError:
        # If direct parse fails, try regex extraction (for LLM responses with extra text)
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                parsed = json.loads(json_match.group())
                parsed['provider'] = llm_response['provider']
                parsed['model'] = llm_response['model']
                if llm_response.get('warnings'):
                    parsed['warnings'] = llm_response['warnings']
                return parsed
        except:
            pass
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "covered_criteria": [],
        "missing_criteria": [c['name'] for c in rubric_criteria],
        "coverage_score": 0,
        "suggestions": ["Unable to parse LLM response"],
        "warnings": llm_response.get('warnings', [])
    }

def ai_analyze_feedback_quality(feedback_text):
    """Analyze feedback quality: specificity, feedforward, tone"""
    prompt = f"""Analyze the quality of the following teaching feedback from three dimensions:

Feedback Content:
"{feedback_text}"

Please evaluate:
1. Specificity: Does the feedback specifically point out specific issues or strengths in the student's work?
2. Feedforward: Does the feedback include specific suggestions for improvement?
3. Tone: Is the feedback professional, encouraging, and constructive?

Please return in JSON format:
{{
    "specificity": {{"score": 1-5, "analysis": "analysis description"}},
    "feedforward": {{"score": 1-5, "analysis": "analysis description"}},
    "tone": {{"score": 1-5, "analysis": "analysis description"}},
    "overall_score": overall score from 1-5,
    "improvement_suggestions": ["list of specific improvement suggestions"]
}}

Return only JSON."""
    
    system_message = "You are an educational feedback quality analysis expert."
    llm_response = call_llm_api(prompt, system_message)
    
    # Check for errors
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "specificity": {"score": 3, "analysis": f"LLM error: {llm_response['error']}"},
            "feedforward": {"score": 3, "analysis": "Unable to analyze"},
            "tone": {"score": 3, "analysis": "Unable to analyze"},
            "overall_score": 3,
            "improvement_suggestions": []
        }
    
    result_text = llm_response.get('content', '')
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            parsed = json.loads(json_match.group())
            parsed['provider'] = llm_response['provider']
            parsed['model'] = llm_response['model']
            if llm_response.get('warnings'):
                parsed['warnings'] = llm_response['warnings']
            return parsed
    except:
        pass
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "specificity": {"score": 3, "analysis": "Unable to parse LLM response"},
        "feedforward": {"score": 3, "analysis": "Unable to analyze"},
        "tone": {"score": 3, "analysis": "Unable to analyze"},
        "overall_score": 3,
        "improvement_suggestions": [],
        "warnings": llm_response.get('warnings', [])
    }

def ai_improve_feedback(original_feedback, improvement_type, rubric_criteria=None, student_work=None):
    """Generate improved version of feedback"""
    context = ""
    if rubric_criteria:
        context += f"\nRubric Criteria: {json.dumps(rubric_criteria, ensure_ascii=False)}"
    if student_work:
        context += f"\nStudent Work Summary: {student_work[:500]}"
    
    improvement_instructions = {
        "specificity": "Make feedback more specific by referencing specific content from student work",
        "feedforward": "Add specific improvement suggestions and next step guidance",
        "tone": "Adjust tone to be more professional, encouraging, and constructive",
        "comprehensive": "Comprehensively improve feedback specificity, feedforward, and tone"
    }
    
    prompt = f"""Please improve the following teaching feedback.

Original Feedback:
"{original_feedback}"
{context}

Improvement Requirements: {improvement_instructions.get(improvement_type, improvement_instructions['comprehensive'])}

Please provide improved feedback while maintaining the instructor's core points but making it more effective. Return only the improved feedback text, no other explanations."""
    
    system_message = "You are an educational feedback improvement expert helping instructors write more effective feedback."
    llm_response = call_llm_api(prompt, system_message)
    
    # Return unified format
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "improved_feedback": ""
        }
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "improved_feedback": llm_response.get('content', ''),
        "warnings": llm_response.get('warnings', [])
    }

def ai_generate_visual_summary(feedback_data, rubric_scores):
    """Generate visual summary data for students"""
    prompt = f"""Based on the following feedback and scores, generate a concise visual summary data.

Feedback Content: {feedback_data}
Score Details: {json.dumps(rubric_scores, ensure_ascii=False)}

Please return in JSON format:
{{
    "strengths": ["list of strengths, max 3"],
    "improvements": ["list of areas for improvement, max 3"],
    "overall_comment": "one sentence summary",
    "encouragement": "encouraging closing remark"
}}

Return only JSON."""
    
    system_message = "You are an educational summary generation expert."
    llm_response = call_llm_api(prompt, system_message)
    
    # Check for errors
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "strengths": [],
            "improvements": [],
            "overall_comment": f"LLM error: {llm_response['error']}",
            "encouragement": ""
        }
    
    result_text = llm_response.get('content', '')
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            parsed = json.loads(json_match.group())
            parsed['provider'] = llm_response['provider']
            parsed['model'] = llm_response['model']
            if llm_response.get('warnings'):
                parsed['warnings'] = llm_response['warnings']
            return parsed
    except:
        pass
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "strengths": ["Good performance"],
        "improvements": ["Keep improving"],
        "overall_comment": "Overall good work",
        "encouragement": "Keep it up!",
        "warnings": llm_response.get('warnings', [])
    }

def ai_generate_video_script(feedback_data, rubric_scores, student_name):
    """Generate video feedback script"""
    prompt = f"""Generate a video feedback script for student {student_name} (about 150-200 words).

Feedback Content: {feedback_data}
Score Details: {json.dumps(rubric_scores, ensure_ascii=False)}

Script Structure:
1. Greeting and overall evaluation
2. 2-3 strengths (based on rubric criteria)
3. 2-3 improvement suggestions (specific and actionable)
4. Encouraging closing

Please generate a conversational, friendly script suitable for video recording. Return only the script content."""
    
    system_message = "You are an educational video script writing expert. Please write in a friendly and natural tone."
    llm_response = call_llm_api(prompt, system_message, max_tokens=500)
    
    # Return unified format
    if llm_response.get('error'):
        return {
            "error": llm_response['error'],
            "provider": llm_response['provider'],
            "script": ""
        }
    
    return {
        "provider": llm_response['provider'],
        "model": llm_response['model'],
        "script": llm_response.get('content', ''),
        "warnings": llm_response.get('warnings', [])
    }

# All routes are now in blueprints (app/routes/)
# Routes are registered in app/__init__.py via create_app()

# ==================== Assignment APIs ====================

@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    """Get all assignments"""
    assignments = load_json(ASSIGNMENTS_FILE)
    return jsonify(assignments), 200

@app.route('/api/assignments', methods=['POST'])
def create_assignment():
    """Create new assignment"""
    data = request.get_json()
    assignments = load_json(ASSIGNMENTS_FILE)
    
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
    save_json(ASSIGNMENTS_FILE, assignments)
    
    return jsonify({'message': 'Assignment created successfully', 'assignment': assignment}), 201

# ==================== Rubric APIs ====================

@app.route('/api/rubrics', methods=['GET'])
def get_rubrics():
    """Get all rubrics"""
    rubrics = load_json(RUBRICS_FILE)
    return jsonify(rubrics), 200

@app.route('/api/rubrics', methods=['POST'])
def create_rubric():
    """Create new rubric"""
    data = request.get_json()
    rubrics = load_json(RUBRICS_FILE)
    
    rubric = {
        'id': str(uuid.uuid4())[:8],
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'criteria': data.get('criteria', []),
        'created_at': datetime.now().isoformat()
    }
    
    rubrics.append(rubric)
    save_json(RUBRICS_FILE, rubrics)
    
    return jsonify({'message': 'Rubric created successfully', 'rubric': rubric}), 201

# ==================== Submission APIs ====================

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions with optional filtering"""
    submissions = load_json(SUBMISSIONS_FILE)
    
    assignment_id = request.args.get('assignment_id')
    student_id = request.args.get('student_id')
    status = request.args.get('status')
    
    if assignment_id:
        submissions = [s for s in submissions if s.get('assignment_id') == assignment_id]
    if student_id:
        submissions = [s for s in submissions if s.get('student_id') == student_id]
    if status:
        submissions = [s for s in submissions if s.get('status') == status]
    
    return jsonify(submissions), 200

@app.route('/api/submissions', methods=['POST'])
def create_submission():
    """Create new submission (student submits work)"""
    data = request.get_json()
    submissions = load_json(SUBMISSIONS_FILE)
    
    submission = {
        'id': str(uuid.uuid4())[:8],
        'assignment_id': data.get('assignment_id', ''),
        'student_id': data.get('student_id', ''),
        'student_name': data.get('student_name', ''),
        'content': data.get('content', ''),
        'submitted_at': datetime.now().isoformat(),
        'status': 'pending',  # pending, grading, graded
        'feedback': None,
        'rubric_scores': None,
        'visual_summary': None,
        'video_script': None,
        'feedback_quality': None,
        'graded_at': None
    }
    
    submissions.append(submission)
    save_json(SUBMISSIONS_FILE, submissions)
    
    return jsonify({'message': 'Submission created successfully', 'submission': submission}), 201

@app.route('/api/submissions/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    """Get specific submission"""
    submissions = load_json(SUBMISSIONS_FILE)
    submission = next((s for s in submissions if s['id'] == submission_id), None)
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    return jsonify(submission), 200

@app.route('/api/submissions/<submission_id>/feedback', methods=['PUT'])
def update_submission_feedback(submission_id):
    """Update submission with feedback (teacher grades)"""
    data = request.get_json()
    submissions = load_json(SUBMISSIONS_FILE)
    
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
        # Only store if no error
        if not visual_summary.get('error'):
            submission['visual_summary'] = visual_summary
        
        video_script_result = ai_generate_video_script(
            submission['feedback'],
            submission['rubric_scores'],
            submission['student_name']
        )
        # Only store if no error
        if not video_script_result.get('error'):
            submission['video_script'] = video_script_result.get('script', '')
    
    save_json(SUBMISSIONS_FILE, submissions)
    
    return jsonify({'message': 'Feedback saved successfully', 'submission': submission}), 200

# ==================== AI Analysis APIs ====================

@app.route('/api/ai/check-alignment', methods=['POST'])
def check_alignment():
    """Check feedback alignment with rubric"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    result = ai_check_rubric_alignment(feedback, rubric_criteria)
    
    # Return 503 if LLM not configured
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(result), 200

@app.route('/api/ai/analyze-quality', methods=['POST'])
def analyze_quality():
    """Analyze feedback quality"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    
    result = ai_analyze_feedback_quality(feedback)
    
    # Return 503 if LLM not configured
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(result), 200

@app.route('/api/ai/improve-feedback', methods=['POST'])
def improve_feedback():
    """Get AI suggestions to improve feedback"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    improvement_type = data.get('type', 'comprehensive')
    rubric_criteria = data.get('rubric_criteria', None)
    student_work = data.get('student_work', None)
    
    result = ai_improve_feedback(feedback, improvement_type, rubric_criteria, student_work)
    
    # Return 503 if LLM not configured
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured",
            "improved_feedback": ""
        }), 503
    
    return jsonify(result), 200

@app.route('/api/ai/generate-summary', methods=['POST'])
def generate_summary():
    """Generate visual summary for student"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_scores = data.get('rubric_scores', {})
    
    summary = ai_generate_visual_summary(feedback, rubric_scores)
    
    # Return 503 if LLM not configured
    if summary.get('error'):
        return jsonify({
            "error": summary['error'],
            "provider": summary.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    return jsonify(summary), 200

@app.route('/api/ai/generate-script', methods=['POST'])
def generate_script():
    """Generate video feedback script"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rubric_scores = data.get('rubric_scores', {})
    student_name = data.get('student_name', 'Student')
    
    result = ai_generate_video_script(feedback, rubric_scores, student_name)
    
    # Return 503 if LLM not configured
    if result.get('error'):
        return jsonify({
            "error": result['error'],
            "provider": result.get('provider', 'unknown'),
            "message": "LLM not configured",
            "script": ""
        }), 503
    
    return jsonify(result), 200

@app.route('/api/ai/analyze-work', methods=['POST'])
def analyze_work():
    """Analyze student work structure and content"""
    data = request.get_json()
    content = data.get('content', '')
    
    analysis = analyze_student_work(content)
    
    # Log the analysis
    log_activity("work_analysis", data.get('teacher_id', 'unknown'), {
        "submission_id": data.get('submission_id'),
        "word_count": analysis['word_count']
    })
    
    return jsonify(analysis), 200

@app.route('/api/ai/suggest-scores', methods=['POST'])
def suggest_scores():
    """AI suggests rubric scores based on student work"""
    data = request.get_json()
    student_work = data.get('student_work', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    suggestions = ai_suggest_scores(student_work, rubric_criteria)
    
    # Return 503 if LLM not configured
    if suggestions.get('error'):
        return jsonify({
            "error": suggestions['error'],
            "provider": suggestions.get('provider', 'unknown'),
            "message": "LLM not configured"
        }), 503
    
    # Log the suggestion
    log_activity("score_suggestion", data.get('teacher_id', 'unknown'), {
        "submission_id": data.get('submission_id'),
        "suggestions_count": len(suggestions.get('suggestions', []))
    })
    
    return jsonify(suggestions), 200

@app.route('/api/ai/detailed-analysis', methods=['POST'])
def detailed_analysis():
    """Comprehensive feedback analysis with coverage details"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    student_work = data.get('student_work', '')
    rubric_criteria = data.get('rubric_criteria', [])
    
    analysis = analyze_feedback_detailed(feedback, student_work, rubric_criteria)
    
    # Log the analysis
    log_activity("detailed_analysis", data.get('teacher_id', 'unknown'), {
        "submission_id": data.get('submission_id'),
        "overall_coverage": analysis['overall_coverage'],
        "flags": analysis['flags']
    })
    
    return jsonify(analysis), 200

# ==================== Engagement Tracking APIs ====================

@app.route('/api/engagement/track', methods=['POST'])
def track_student_engagement():
    """Track student engagement with feedback"""
    data = request.get_json()
    student_id = data.get('student_id', '')
    submission_id = data.get('submission_id', '')
    action = data.get('action', '')
    details = data.get('details', {})
    
    record = track_engagement(student_id, submission_id, action, details)
    return jsonify(record), 200

@app.route('/api/engagement/stats', methods=['GET'])
def get_engagement_stats():
    """Get engagement statistics"""
    engagement = load_json(ENGAGEMENT_FILE)
    
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

@app.route('/api/logs', methods=['GET'])
def get_activity_logs():
    """Get activity logs with optional filtering"""
    logs = load_json(LOGS_FILE)
    
    log_type = request.args.get('type')
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 100, type=int)
    
    if log_type:
        logs = [l for l in logs if l.get('type') == log_type]
    if user_id:
        logs = [l for l in logs if l.get('user_id') == user_id]
    
    # Sort by timestamp descending and limit
    logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    return jsonify(logs), 200

@app.route('/api/logs/summary', methods=['GET'])
def get_logs_summary():
    """Get summary of activity logs"""
    logs = load_json(LOGS_FILE)
    
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

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get system configuration"""
    config = get_system_config()
    return jsonify(config), 200

@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update system configuration"""
    data = request.get_json()
    config = get_system_config()
    
    # Update features
    if 'features' in data:
        config['features'].update(data['features'])
    
    # Update thresholds
    if 'thresholds' in data:
        config['thresholds'].update(data['thresholds'])
    
    # Update limits
    if 'limits' in data:
        config['limits'].update(data['limits'])
    
    save_json(CONFIG_FILE, config)
    
    log_activity("config_updated", "admin", {"changes": data})
    
    return jsonify({'message': 'Configuration updated', 'config': config}), 200

# ==================== Statistics APIs ====================

@app.route('/api/stats/teacher', methods=['GET'])
def get_teacher_stats():
    """Get teacher dashboard statistics"""
    submissions = load_json(SUBMISSIONS_FILE)
    assignments = load_json(ASSIGNMENTS_FILE)
    
    stats = {
        'total_assignments': len(assignments),
        'total_submissions': len(submissions),
        'pending_grading': len([s for s in submissions if s['status'] == 'pending']),
        'graded': len([s for s in submissions if s['status'] == 'graded']),
        'average_score': 0
    }
    
    # Calculate average score
    graded = [s for s in submissions if s.get('rubric_scores')]
    if graded:
        total_score = 0
        count = 0
        for s in graded:
            scores = s['rubric_scores']
            if isinstance(scores, dict) and 'total' in scores:
                total_score += scores['total']
                count += 1
        if count > 0:
            stats['average_score'] = round(total_score / count, 1)
    
    return jsonify(stats), 200

@app.route('/api/stats/student/<student_id>', methods=['GET'])
def get_student_stats(student_id):
    """Get student statistics"""
    submissions = load_json(SUBMISSIONS_FILE)
    student_submissions = [s for s in submissions if s.get('student_id') == student_id]
    
    stats = {
        'total_submissions': len(student_submissions),
        'graded': len([s for s in student_submissions if s['status'] == 'graded']),
        'pending': len([s for s in student_submissions if s['status'] == 'pending']),
        'submissions': student_submissions
    }
    
    return jsonify(stats), 200

# ==================== User APIs ====================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = load_json(USERS_FILE)
    return jsonify(users), 200

# ==================== Demo Data ====================

@app.route('/api/demo/init', methods=['POST'])
def init_demo_data():
    """Initialize demo data for testing"""
    # Create sample rubric
    rubrics = [{
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
    }]
    save_json(RUBRICS_FILE, rubrics)
    
    # Create sample assignment
    assignments = [{
        'id': 'A001',
        'title': 'AI Ethics Analysis Essay',
        'description': 'Write a 1500-word essay analyzing ethical issues in AI development and provide your perspectives and recommendations.',
        'course_id': 'CS101',
        'due_date': '2025-12-20',
        'rubric_id': 'R001',
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }]
    save_json(ASSIGNMENTS_FILE, assignments)
    
    # Create sample submissions
    submissions = [
        {
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
            'status': 'pending',
            'feedback': None,
            'rubric_scores': None,
            'visual_summary': None,
            'video_script': None,
            'graded_at': None
        },
        {
            'id': 'SUB002',
            'assignment_id': 'A001',
            'student_id': 'S002',
            'student_name': 'Emily Johnson',
            'content': '''Thoughts on AI Ethics

Artificial intelligence is important. It has both advantages and disadvantages.

The advantage is that it can help us do many things. The disadvantage is that there might be problems.

I think we should develop AI well, but also pay attention to problems.''',
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending',
            'feedback': None,
            'rubric_scores': None,
            'visual_summary': None,
            'video_script': None,
            'graded_at': None
        }
    ]
    save_json(SUBMISSIONS_FILE, submissions)
    
    return jsonify({'message': 'Demo data initialized successfully'}), 200

if __name__ == '__main__':
    # Configuration from environment variables
    from app.config import Config
    debug_mode = Config.DEBUG
    port = Config.WEB_PORT
    
    # Run with logging to stdout (container-friendly)
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
