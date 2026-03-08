"""Enhanced tests for CSCL Spec Validation API - C1-1.1"""
import pytest
import json
import os
from app.utils.schema_validator import validate_normalized_spec


# ==================== Permission Tests ====================

def test_validate_spec_public_false_no_auth(client, app):
    """Test: public=false, no auth -> 401"""
    original = app.config.get('SPEC_VALIDATE_PUBLIC')
    app.config['SPEC_VALIDATE_PUBLIC'] = False
    try:
        spec_data = {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'ML',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90,
                'description': 'Test context.'
            },
            'learning_objectives': {
                'knowledge': ['Test'],
                'skills': ['Test']
            },
            'task_requirements': {
                'task_type': 'structured_debate',
                'expected_output': 'test',
                'collaboration_form': 'group',
                'requirements_text': 'Test requirements.'
            }
        }
        resp = client.post('/api/cscl/spec/validate', json=spec_data)
        assert resp.status_code == 401
        data = json.loads(resp.data)
        assert 'error' in data
        assert data.get('code') == 'AUTH_REQUIRED'
    finally:
        if original is not None:
            app.config['SPEC_VALIDATE_PUBLIC'] = original
        else:
            app.config.pop('SPEC_VALIDATE_PUBLIC', None)


def test_validate_spec_public_false_student(client, app, seed_users):
    """Test: public=false, student -> 403"""
    original = app.config.get('SPEC_VALIDATE_PUBLIC')
    app.config['SPEC_VALIDATE_PUBLIC'] = False
    try:
        client.post('/api/auth/login', json={'user_id': 'S001', 'password': 'student123'})
        spec_data = {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'ML',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90,
                'description': 'Test context.'
            },
            'learning_objectives': {
                'knowledge': ['Test'],
                'skills': ['Test']
            },
            'task_requirements': {
                'task_type': 'structured_debate',
                'expected_output': 'test',
                'collaboration_form': 'group',
                'requirements_text': 'Test requirements.'
            }
        }
        resp = client.post('/api/cscl/spec/validate', json=spec_data)
        assert resp.status_code == 403
        data = json.loads(resp.data)
        assert 'error' in data
        assert data.get('code') == 'PERMISSION_DENIED'
    finally:
        app.config['SPEC_VALIDATE_PUBLIC'] = original


def test_validate_spec_public_false_teacher(client, app, seed_users):
    """Test: public=false, teacher -> 200"""
    import os
    import importlib
    import app.config
    
    original_value = os.environ.get('SPEC_VALIDATE_PUBLIC', 'false')
    os.environ['SPEC_VALIDATE_PUBLIC'] = 'false'
    importlib.reload(app.config)
    
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }

    resp = client.post('/api/cscl/spec/validate', json=spec_data)

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    
    # Restore
    if original_value:
        os.environ['SPEC_VALIDATE_PUBLIC'] = original_value
    else:
        os.environ.pop('SPEC_VALIDATE_PUBLIC', None)
    importlib.reload(app.config)


def test_validate_spec_public_true_no_auth(client, app):
    """Test: public=true, no auth -> 200"""
    import os
    import importlib
    import app.config
    
    original_value = os.environ.get('SPEC_VALIDATE_PUBLIC', 'false')
    os.environ['SPEC_VALIDATE_PUBLIC'] = 'true'
    importlib.reload(app.config)
    
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }

    resp = client.post('/api/cscl/spec/validate', json=spec_data)

    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    
    # Restore
    if original_value:
        os.environ['SPEC_VALIDATE_PUBLIC'] = original_value
    else:
        os.environ.pop('SPEC_VALIDATE_PUBLIC', None)
    importlib.reload(app.config)


# ==================== Error Code Tests ====================

def test_invalid_json_returns_400(client):
    """Test: Invalid JSON -> 400"""
    resp = client.post(
        '/api/cscl/spec/validate',
        data='{invalid json}',
        content_type='application/json'
    )
    
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data.get('code') == 'INVALID_JSON' or data.get('code') == 'MISSING_BODY'


def test_validation_failure_returns_422(client):
    """Test: Business rule validation failure -> 422"""
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'invalid_mode',  # Invalid
            'duration': 90,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }

    resp = client.post('/api/cscl/spec/validate', json=spec_data)

    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data['valid'] is False
    assert data.get('code') == 'VALIDATION_FAILED'


# ==================== Boundary Value Tests ====================

def test_class_size_minimum(client):
    """Test: class_size = 1 (minimum valid)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 1,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200


def test_class_size_zero(client):
    """Test: class_size = 0 (invalid)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 0,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422


def test_class_size_negative(client):
    """Test: class_size = -1 (invalid)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': -1,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422


def test_duration_minimum(client):
    """Test: duration = 1 (minimum valid)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 1,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200


def test_duration_zero(client):
    """Test: duration = 0 (invalid)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 0,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422


def test_very_long_string(client):
    """Test: Very long string (10000 chars)"""
    long_string = 'A' * 10000
    spec_data = {
        'course_context': {
            'subject': long_string,
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    # Should accept (no length limit in schema)
    assert resp.status_code == 200


def test_unknown_fields_allowed(client):
    """Test: Unknown fields are ignored (not rejected)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 60,
            'unknown_field': 'should be ignored',
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        },
        'unknown_top_level': 'should be ignored'
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    # Should accept (unknown fields are ignored)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['valid'] is True
    # Unknown fields should not appear in normalized_spec
    assert 'unknown_field' not in data['normalized_spec']['course_context']
    assert 'unknown_top_level' not in data['normalized_spec']


def test_empty_array_in_optional(client):
    """Test: Empty array in optional field (disposition)"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test'],
            'disposition': []  # Empty array
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200


def test_nested_empty_object(client):
    """Test: Nested empty object in constraints"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'sync',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test requirements.'
        },
        'constraints': {}  # Empty object
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200


def test_all_invalid_enums(client):
    """Test: All invalid enum values"""
    spec_data = {
        'course_context': {
            'subject': 'Test',
            'topic': 'Test',
            'class_size': 30,
            'mode': 'invalid_mode',
            'duration': 60,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'invalid_task',
            'expected_output': 'test',
            'collaboration_form': 'invalid_form'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert len(data['issues']) >= 3  # Should have issues for all invalid enums


# ==================== Schema Validation Tests ====================

def test_normalized_spec_schema_compliance(client):
    """Test: normalized_spec complies with JSON schema"""
    spec_data = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Undergraduate ML course.'
        },
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

    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200
    
    data = json.loads(resp.data)
    assert data['valid'] is True
    assert data['normalized_spec'] is not None
    
    # Validate against schema
    is_valid, error = validate_normalized_spec(data['normalized_spec'])
    assert is_valid, f"Schema validation failed: {error}"


def test_normalized_spec_with_optional_fields_schema_compliance(client):
    """Test: normalized_spec with optional fields complies with schema"""
    spec_data = {
        'course_context': {
            'subject': 'Learning Sciences',
            'topic': 'Collaborative Learning',
            'class_size': 25,
            'mode': 'async',
            'duration': 120,
            'description': 'Test context.'
        },
        'learning_objectives': {
            'knowledge': ['Understand collaboration'],
            'skills': ['Facilitate discussions'],
            'disposition': ['Value diversity']
        },
        'task_requirements': {
            'task_type': 'collaborative_writing',
            'expected_output': 'group essay',
            'collaboration_form': 'pair'
        },
        'constraints': {
            'tools': ['Google Docs'],
            'timebox': 60
        },
        'rubric_preferences': {
            'criteria': ['Clarity'],
            'emphasis': 'Focus on evidence'
        }
    }
    
    resp = client.post('/api/cscl/spec/validate', json=spec_data)
    assert resp.status_code == 200
    
    data = json.loads(resp.data)
    assert data['valid'] is True
    
    # Validate against schema
    is_valid, error = validate_normalized_spec(data['normalized_spec'])
    assert is_valid, f"Schema validation failed: {error}"
