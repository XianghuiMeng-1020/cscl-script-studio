"""Utility functions for the application"""
import json
import os
import uuid
from datetime import datetime
from app.config import Config


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


# Ensure data directory exists
os.makedirs(Config.DATA_DIR, exist_ok=True)


# Initialize data files
def init_data_file(filepath, default_data):
    """Initialize a data file with default data if it doesn't exist"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)


# Initialize all data files with sample data
init_data_file(Config.ASSIGNMENTS_FILE, [])
init_data_file(Config.SUBMISSIONS_FILE, [])
init_data_file(Config.RUBRICS_FILE, [])
init_data_file(Config.USERS_FILE, {
    "teachers": [
        {"id": "T001", "name": "Prof. Smith", "email": "smith@university.edu", "courses": ["CS101", "CS201"]}
    ],
    "students": [
        {"id": "S001", "name": "John Smith", "email": "john@student.edu", "courses": ["CS101"]},
        {"id": "S002", "name": "Emily Johnson", "email": "emily@student.edu", "courses": ["CS101"]},
        {"id": "S003", "name": "Michael Brown", "email": "michael@student.edu", "courses": ["CS101"]}
    ]
})
init_data_file(Config.LOGS_FILE, [])
init_data_file(Config.CONFIG_FILE, DEFAULT_CONFIG)
init_data_file(Config.ENGAGEMENT_FILE, {})


def load_json(filepath):
    """Load JSON data from file"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_json(filepath, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_activity(activity_type, user_id, details):
    """Log system activity for analytics"""
    logs = load_json(Config.LOGS_FILE)
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "type": activity_type,
        "user_id": user_id,
        "details": details
    }
    logs.append(log_entry)
    save_json(Config.LOGS_FILE, logs)
    return log_entry


def get_system_config():
    """Get current system configuration"""
    config = load_json(Config.CONFIG_FILE)
    if not config:
        config = DEFAULT_CONFIG
        save_json(Config.CONFIG_FILE, config)
    return config


def analyze_student_work(content):
    """Analyze student submission structure and content"""
    import re
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


def analyze_feedback_detailed(feedback_text, student_work, rubric_criteria):
    """Comprehensive feedback analysis with semantic matching"""
    import re
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


def track_engagement(student_id, submission_id, action, details=None):
    """Track student engagement with feedback"""
    engagement = load_json(Config.ENGAGEMENT_FILE)
    if not isinstance(engagement, dict):
        engagement = {}
    
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
        record["time_spent_seconds"] += details.get("seconds", 0) if details else 0
    
    record["actions"].append({
        "action": action,
        "timestamp": timestamp,
        "details": details
    })
    
    engagement[key] = record
    save_json(Config.ENGAGEMENT_FILE, engagement)
    return record
