"""Tests for CSCL Spec Validation API"""
import pytest
import json
from app.services.spec_validator import SpecValidator


def test_valid_spec_basic(client):
    """Test 1: Valid basic spec returns valid=true"""
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Undergraduate course; learners have basic stats.'
        },
        'learning_objectives': {
            'knowledge': ['Understand ML basics'],
            'skills': ['Apply algorithms']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'argument',
            'collaboration_form': 'group',
            'requirements_text': 'Minimum 2 evidence sources; respond to counterargument.'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    assert len(data['issues']) == 0
    assert data['normalized_spec'] is not None
    assert 'course_context' in data['normalized_spec']


def test_valid_spec_with_optional_fields(client):
    """Test 2: Valid spec with optional fields returns valid=true"""
    spec_data = {
        'course_context': {
            'subject': 'Learning Sciences',
            'topic': 'Collaborative Learning',
            'class_size': 25,
            'mode': 'async',
            'duration': 120,
            'description': 'Graduate seminar; mixed backgrounds.'
        },
        'learning_objectives': {
            'knowledge': ['Understand collaboration principles'],
            'skills': ['Facilitate group discussions'],
            'disposition': ['Value diverse perspectives']
        },
        'task_requirements': {
            'task_type': 'perspective_synthesis',
            'expected_output': 'group essay',
            'collaboration_form': 'pair',
            'requirements_text': 'Synthesize at least 3 sources; group artifact required.'
        },
        'constraints': {
            'tools': ['Google Docs', 'Zoom'],
            'timebox': 60
        },
        'rubric_preferences': {
            'criteria': ['Clarity', 'Evidence'],
            'emphasis': 'Focus on evidence quality'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    assert len(data['issues']) == 0
    assert data['normalized_spec'] is not None


def test_invalid_spec_missing_course_context(client):
    """Test 3: Invalid spec missing course_context returns valid=false"""
    spec_data = {
        'learning_objectives': {
            'knowledge': ['Understand ML basics'],
            'skills': ['Apply algorithms']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'argument',
            'collaboration_form': 'group',
            'requirements_text': 'Minimum evidence required.'
        }
    }

    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )

    assert resp.status_code == 422  # Changed from 400 to 422 for validation failures
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert len(data['issues']) > 0
    assert 'course_context' in ' '.join(data['issues']).lower()
    assert data['normalized_spec'] is None


def test_invalid_spec_empty_fields(client):
    """Test 4: Invalid spec with empty required fields returns valid=false"""
    spec_data = {
        'course_context': {
            'subject': '',  # Empty
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Some context'
        },
        'learning_objectives': {
            'knowledge': [],  # Empty
            'skills': ['Apply algorithms']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'argument',
            'collaboration_form': 'group',
            'requirements_text': 'Some requirements'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 422  # Changed from 400 to 422 for validation failures
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert len(data['issues']) > 0
    assert data['normalized_spec'] is None


def test_invalid_spec_invalid_mode(client):
    """Test 5: Invalid spec with invalid mode returns valid=false"""
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'invalid_mode',  # Invalid
            'duration': 90,
            'description': 'Undergraduate course'
        },
        'learning_objectives': {
            'knowledge': ['Understand ML basics'],
            'skills': ['Apply algorithms']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'argument',
            'collaboration_form': 'group',
            'requirements_text': 'Minimum evidence'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 422  # Changed to 422 for validation failures
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert len(data['issues']) > 0
    assert 'mode' in ' '.join(data['issues']).lower()
    assert data['normalized_spec'] is None


def test_invalid_spec_invalid_task_type(client):
    """Test 6: Invalid spec with invalid task_type returns valid=false"""
    spec_data = {
        'course_context': {
            'subject': 'Humanities',
            'topic': 'Literary Analysis',
            'class_size': 20,
            'mode': 'sync',
            'duration': 60,
            'description': 'Graduate seminar'
        },
        'learning_objectives': {
            'knowledge': ['Understand literary devices'],
            'skills': ['Analyze texts']
        },
        'task_requirements': {
            'task_type': 'invalid_task',  # Invalid
            'expected_output': 'analysis',
            'collaboration_form': 'group',
            'requirements_text': 'Group artifact required'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 422  # Changed to 422 for validation failures
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert len(data['issues']) > 0
    assert 'task_type' in ' '.join(data['issues']).lower()
    assert data['normalized_spec'] is None


def test_valid_spec_humanities(client):
    """Test 7: Valid Humanities spec returns valid=true"""
    spec_data = {
        'course_context': {
            'subject': 'Humanities',
            'topic': 'Literary Analysis',
            'class_size': 20,
            'mode': 'sync',
            'duration': 60,
            'description': 'Graduate seminar on literary analysis.'
        },
        'learning_objectives': {
            'knowledge': ['Understand literary devices'],
            'skills': ['Analyze texts', 'Write critiques']
        },
        'task_requirements': {
            'task_type': 'evidence_comparison',
            'expected_output': 'peer feedback',
            'collaboration_form': 'pair',
            'requirements_text': 'Each student provides feedback on two peers.'
        }
    }
    
    resp = client.post(
        '/api/cscl/spec/validate',
        json=spec_data
    )
    
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    assert len(data['issues']) == 0
    assert data['normalized_spec'] is not None


def test_empty_request_body(client):
    """Test 8: Empty request body returns error"""
    resp = client.post(
        '/api/cscl/spec/validate',
        json={}
    )
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert len(data['issues']) > 0


def test_invalid_spec_missing_course_context_description(client):
    """Missing course_context.description => 422 and field can be located"""
    spec_data = {
        'course_context': {
            'subject': 'DS',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90
            # description missing
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'O',
            'collaboration_form': 'group',
            'requirements_text': 'Some requirements'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert any('course_context.description' in i or 'description' in i for i in data['issues'])


def test_invalid_spec_missing_task_requirements_text(client):
    """Missing task_requirements.requirements_text => 422 and field can be located"""
    spec_data = {
        'course_context': {
            'subject': 'DS',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Course context here'
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'O',
            'collaboration_form': 'group'
            # requirements_text missing
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert any('requirements_text' in i or 'task_requirements' in i for i in data['issues'])


def test_fill_demo_spec_validates(client):
    """Fill Demo Data payload (canonical shape) => validate 200 / success"""
    demo_spec = {
        'course_context': {
            'subject': 'Introduction to Data Science',
            'topic': 'Algorithmic Fairness in Education',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Undergraduate data science course; learners have basic statistics. 90-min synchronous session for collaborative argumentation.'
        },
        'learning_objectives': {
            'knowledge': ['Explain basic fairness metrics', 'Compare trade-offs between accuracy and fairness'],
            'skills': ['Construct evidence-based group arguments']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'Group argument map; 300-word joint reflection',
            'collaboration_form': 'group',
            'requirements_text': 'Minimum 2 evidence sources per position; each group must respond to at least one counterargument; group artifact: shared argument map and 300-word reflection.'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=demo_spec)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data.get('valid') is True
    assert data.get('normalized_spec') is not None


def test_task_types_api(client):
    """GET /api/cscl/task-types returns config with default 4 types; UI and backend share same list"""
    resp = client.get('/api/cscl/task-types')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'task_types' in data
    types = data['task_types']
    ids = [t['id'] for t in types if t.get('id')]
    for expected in ['structured_debate', 'evidence_comparison', 'perspective_synthesis', 'claim_counterclaim_roleplay']:
        assert expected in ids, 'default task type %s should be in config' % expected
    assert 'description' in data or any('description' in t for t in types)


# --- Validate independent from Fill Demo and file upload (BLOCKER acceptance) ---

def test_manual_input_validate_pass_without_demo(client):
    """Manually filling required fields (no Fill Demo, no upload) must return 200 on /api/cscl/spec/validate."""
    spec = {
        'course_context': {
            'subject': 'My Course',
            'topic': 'My Topic',
            'class_size': 20,
            'mode': 'sync',
            'duration': 60,
            'description': 'Manually entered course setting and learner profile for this activity.'
        },
        'learning_objectives': {
            'knowledge': ['First knowledge objective'],
            'skills': ['First skill objective']
        },
        'task_requirements': {
            'task_type': 'perspective_synthesis',
            'expected_output': 'Group summary document',
            'collaboration_form': 'pair',
            'requirements_text': 'Manually entered collaboration and evidence requirements.'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data.get('valid') is True
    assert data.get('normalized_spec') is not None


def test_validate_pass_without_upload(client):
    """Uploading documents is NOT a prerequisite for spec validation; validate can pass with no upload."""
    spec = {
        'course_context': {
            'subject': 'No Upload Course',
            'topic': 'Topic Without Documents',
            'class_size': 15,
            'mode': 'async',
            'duration': 45,
            'description': 'Context without any prior document upload.'
        },
        'learning_objectives': {
            'knowledge': ['K1'],
            'skills': ['S1']
        },
        'task_requirements': {
            'task_type': 'claim_counterclaim_roleplay',
            'expected_output': 'Role summary',
            'collaboration_form': 'whole_class',
            'requirements_text': 'Requirements without upload dependency.'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data.get('valid') is True


def test_fill_demo_not_required_for_success(client):
    """Fill Demo is optional helper only; success does not require using Fill Demo."""
    # Payload that looks nothing like the demo (different structure/content) but is valid
    spec = {
        'course_context': {
            'subject': 'Philosophy 101',
            'topic': 'Ethics of AI',
            'class_size': 25,
            'mode': 'async',
            'duration': 120,
            'description': 'Intro philosophy; students have no prior AI ethics background.'
        },
        'learning_objectives': {
            'knowledge': ['Define key ethics terms', 'Identify stakeholders'],
            'skills': ['Argue from multiple perspectives']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'Position statement and rebuttal',
            'collaboration_form': 'group',
            'requirements_text': 'Two sources per side; one rebuttal per group required.'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data.get('valid') is True
    assert data['normalized_spec']['course_context']['topic'] == 'Ethics of AI'


def test_422_returns_field_paths_and_frontend_maps_them(client):
    """On 422, backend returns machine-readable field_paths; frontend can map to first invalid field."""
    spec_missing_description = {
        'course_context': {
            'subject': 'S',
            'topic': 'T',
            'class_size': 10,
            'mode': 'sync',
            'duration': 60
            # description missing
        },
        'learning_objectives': {'knowledge': ['K'], 'skills': ['S']},
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'O',
            'collaboration_form': 'group',
            'requirements_text': 'Req'
        }
    }
    resp = client.post('/api/cscl/spec/validate', json=spec_missing_description)
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data.get('valid') is False
    assert 'field_paths' in data
    field_paths = data['field_paths']
    assert isinstance(field_paths, list)
    assert len(field_paths) >= 1
    assert 'course_context.description' in field_paths
    # First path should be mappable to a frontend id (e.g. specCourseContext)
    first_path = field_paths[0]
    assert first_path in (
        'course_context', 'course_context.subject', 'course_context.topic',
        'course_context.class_size', 'course_context.mode', 'course_context.duration',
        'course_context.description', 'learning_objectives.knowledge', 'learning_objectives.skills',
        'task_requirements.task_type', 'task_requirements.expected_output',
        'task_requirements.collaboration_form', 'task_requirements.requirements_text'
    )
