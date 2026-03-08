"""AI service functions"""
import json
import re
from app.services.llm_provider import get_llm_provider
from app.utils import analyze_student_work


# LLM Provider initialization (lazy loading)
_llm_provider = None

def get_provider():
    """Get LLM provider instance (singleton)"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider()
    return _llm_provider


def call_llm_api(prompt, system_message="You are a helpful assistant.", 
                 max_tokens=1000, temperature=0.7):
    """
    Unified entry point for all LLM API calls
    
    Returns:
        Dict with keys: provider, model, content, warnings, error
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
