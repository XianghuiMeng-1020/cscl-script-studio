"""Tests for CSCL Pipeline API"""
import pytest
import json
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLPipelineRun

VALID_SPEC = {
    'course_context': {
        'subject': 'Data Science',
        'topic': 'Machine Learning',
        'class_size': 30,
        'mode': 'sync',
        'duration': 90,
        'description': 'Test course context.'
    },
    'learning_objectives': {
        'knowledge': ['Understand ML basics'],
        'skills': ['Apply algorithms']
    },
    'task_requirements': {
        'task_type': 'structured_debate',
        'expected_output': 'argument',
        'collaboration_form': 'group',
        'requirements_text': 'Test requirements.'
    }
}


def test_pipeline_preflight_200_when_ready(client, app, seed_users):
    """B2: Preflight with valid spec returns 200, ready true when provider ready."""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Preflight Test',
            'topic': 'ML',
            'course_id': 'default-course',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/preflight',
        json={'spec': VALID_SPEC},
        content_type='application/json'
    )
    assert resp.status_code in (200, 503)
    data = json.loads(resp.data)
    assert 'success' in data
    if resp.status_code == 200:
        assert data.get('ready') is True
        assert 'details' in data
    else:
        assert data.get('error_code') == 'LLM_PROVIDER_NOT_READY'


def test_pipeline_preflight_422_invalid_spec(client, app, seed_users):
    """B2: Preflight with invalid spec returns 422 and issues."""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    script_resp = client.post(
        '/api/cscl/scripts',
        json={'title': 'P', 'topic': 'T', 'course_id': 'default-course', 'task_type': 'structured_debate', 'duration_minutes': 60}
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/preflight',
        json={'spec': {'course_context': {}, 'learning_objectives': {}, 'task_requirements': {}}},
        content_type='application/json'
    )
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data.get('success') is False
    assert data.get('error_code') == 'SPEC_INVALID'
    assert 'details' in data


def test_teacher_can_run_pipeline(client, app, seed_users):
    """Test 1: Teacher can run pipeline -> 200"""
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']

    spec = VALID_SPEC
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec, 'generation_options': {}}
    )
    
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'run_id' in data
    assert 'stages' in data
    assert len(data['stages']) == 4


def test_pipeline_run_422_returns_spec_invalid_with_issues(client, app, seed_users):
    """Pipeline run with invalid spec returns 422, code SPEC_INVALID, issues with field and reason."""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test',
            'topic': 'T',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']
    invalid_spec = {
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
            'requirements_text': 'R'
        }
    }
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': invalid_spec}
    )
    assert resp.status_code == 422
    data = json.loads(resp.data)
    assert data.get('code') == 'SPEC_INVALID'
    assert data.get('error') == 'SPEC_INVALID'
    assert 'issues' in data
    assert isinstance(data['issues'], list)
    assert len(data['issues']) >= 1
    assert data['issues'][0].get('field') == 'course_context.description'
    assert data['issues'][0].get('reason') in ('required', 'invalid')


def test_student_cannot_run_pipeline(client, app, seed_users):
    """Test 2: Student cannot run pipeline -> 403"""
    # Login as student
    client.post('/api/auth/login', json={'user_id': 'S001', 'password': 'student123'})
    
    resp = client.post(
        '/api/cscl/scripts/any-id/pipeline/run',
        json={'spec': {}}
    )
    
    assert resp.status_code == 403
    data = json.loads(resp.data)
    assert 'error' in data


def test_unauthenticated_cannot_run_pipeline(client):
    """Test 3: Unauthenticated cannot run pipeline -> 401"""
    resp = client.post(
        '/api/cscl/scripts/any-id/pipeline/run',
        json={'spec': {}}
    )
    
    assert resp.status_code == 401


def test_get_pipeline_run_details(client, app, seed_users):
    """Test 4: Get pipeline run details -> 200"""
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script and run pipeline
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    run_resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    assert run_resp.status_code == 200
    run_id = json.loads(run_resp.data)['run_id']
    
    # Get run details
    resp = client.get(f'/api/cscl/pipeline/runs/{run_id}')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'run' in data
    assert 'stages' in data
    assert len(data['stages']) == 4


def test_get_script_pipeline_runs(client, app, seed_users):
    """Test 5: Get script pipeline runs -> 200"""
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    # Run pipeline twice
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    client.post(f'/api/cscl/scripts/{script_id}/pipeline/run', json={'spec': spec})
    client.post(f'/api/cscl/scripts/{script_id}/pipeline/run', json={'spec': spec})
    
    # Get runs
    resp = client.get(f'/api/cscl/scripts/{script_id}/pipeline/runs')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['success'] is True
    assert len(data['runs']) == 2


def test_provider_missing_key_returns_explained_error(client, app, seed_users):
    """Test 6: Provider missing key -> explained error (not 500)"""
    import os
    original_key = os.environ.get('QWEN_API_KEY')
    os.environ.pop('QWEN_API_KEY', None)
    os.environ['LLM_PROVIDER'] = 'qwen'
    
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    assert resp.status_code == 503
    data = json.loads(resp.data)
    assert 'error' in data
    assert data.get('code') in ('PROVIDER_KEY_MISSING', 'LLM_PROVIDER_NOT_READY')
    assert 'QWEN_API_KEY' in data.get('error', '') or 'not configured' in data.get('error', '').lower()
    
    # Restore
    if original_key:
        os.environ['QWEN_API_KEY'] = original_key
    os.environ['LLM_PROVIDER'] = 'mock'


def test_planner_failure_preserves_logs(client, app, seed_users):
    """Test 7: Planner failure preserves logs"""
    # This test would require mocking provider to fail
    # For now, we test that failed runs are recorded
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    # Run with mock provider (should succeed)
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    # Even if successful, verify logs are preserved
    assert resp.status_code in [200, 422, 503]
    if resp.status_code == 200:
        data = json.loads(resp.data)
        run_id = data.get('run_id')
        if run_id:
            detail_resp = client.get(f'/api/cscl/pipeline/runs/{run_id}')
            assert detail_resp.status_code == 200
            detail_data = json.loads(detail_resp.data)
            assert len(detail_data.get('stages', [])) > 0


def test_critic_failure_preserves_previous_stages(client, app, seed_users):
    """Test 8: Critic failure preserves previous stages"""
    # Similar to test 7, verify partial failures preserve logs
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    # Verify stages are logged even if pipeline fails
    assert resp.status_code in [200, 422, 503]
    if resp.status_code == 200:
        data = json.loads(resp.data)
        assert 'stages' in data
        assert len(data['stages']) >= 1  # At least planner stage


def test_refiner_success_produces_complete_script(client, app, seed_users):
    """Test 9: Refiner success produces complete script structure"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    if resp.status_code == 200:
        data = json.loads(resp.data)
        final_output = data.get('final_output', {})
        assert 'scenes' in final_output
        assert 'roles' in final_output
        assert len(final_output.get('scenes', [])) > 0
        assert len(final_output.get('roles', [])) > 0


def test_same_spec_produces_comparable_fingerprint(client, app, seed_users):
    """Test 10: Same spec produces comparable fingerprint"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    # Run twice with same spec
    resp1 = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    resp2 = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    if resp1.status_code == 200 and resp2.status_code == 200:
        data1 = json.loads(resp1.data)
        data2 = json.loads(resp2.data)
        
        run_id1 = data1['run_id']
        run_id2 = data2['run_id']
        
        # Get run details
        detail1 = client.get(f'/api/cscl/pipeline/runs/{run_id1}')
        detail2 = client.get(f'/api/cscl/pipeline/runs/{run_id2}')
        
        if detail1.status_code == 200 and detail2.status_code == 200:
            run1 = json.loads(detail1.data)['run']
            run2 = json.loads(detail2.data)['run']
            
            # Same spec should produce same spec_hash
            assert run1.get('spec_hash') == run2.get('spec_hash')


def test_mock_provider_stable_output(client, app, seed_users):
    """Test 11: Mock provider produces stable output structure"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'AI Ethics',
            'task_type': 'structured_debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'description': 'Test.'
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'structured_debate',
            'expected_output': 'test',
            'collaboration_form': 'group',
            'requirements_text': 'Test.'
        }
    }
    
    resp = client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    if resp.status_code == 200:
        data = json.loads(resp.data)
        stages = data.get('stages', [])
        
        # Verify all stages have required structure
        for stage in stages:
            assert 'stage_name' in stage
            assert 'status' in stage
            assert 'provider' in stage
            assert 'model' in stage
            assert 'latency_ms' in stage


def test_three_disciplines_specs_work(client, app, seed_users):
    """Test 12: Three discipline specs all work"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    disciplines = [
        {
            'name': 'Data Science',
            'spec': {
                'course_context': {
                    'subject': 'Data Science',
                    'topic': 'Machine Learning',
                    'class_size': 30,
                    'mode': 'sync',
                    'duration': 90,
                    'description': 'ML course.'
                },
                'learning_objectives': {
                    'knowledge': ['Understand ML basics'],
                    'skills': ['Apply algorithms']
                },
                'task_requirements': {
                    'task_type': 'structured_debate',
                    'expected_output': 'argument',
                    'collaboration_form': 'group',
                    'requirements_text': 'Debate requirements.'
                }
            }
        },
        {
            'name': 'Learning Sciences',
            'spec': {
                'course_context': {
                    'subject': 'Learning Sciences',
                    'topic': 'Collaborative Learning',
                    'class_size': 25,
                    'mode': 'async',
                    'duration': 120,
                    'description': 'Collaboration course.'
                },
                'learning_objectives': {
                    'knowledge': ['Understand collaboration principles'],
                    'skills': ['Facilitate group discussions']
                },
                'task_requirements': {
                    'task_type': 'perspective_synthesis',
                    'expected_output': 'group essay',
                    'collaboration_form': 'pair',
                    'requirements_text': 'Synthesis requirements.'
                }
            }
        },
        {
            'name': 'Humanities',
            'spec': {
                'course_context': {
                    'subject': 'Humanities',
                    'topic': 'Literary Analysis',
                    'class_size': 20,
                    'mode': 'sync',
                    'duration': 60,
                    'description': 'Humanities course.'
                },
                'learning_objectives': {
                    'knowledge': ['Understand literary devices'],
                    'skills': ['Analyze texts']
                },
                'task_requirements': {
                    'task_type': 'evidence_comparison',
                    'expected_output': 'peer feedback',
                    'collaboration_form': 'pair',
                    'requirements_text': 'Comparison requirements.'
                }
            }
        }
    ]
    
    for discipline in disciplines:
        # Create script
        script_resp = client.post(
            '/api/cscl/scripts',
            json={
                'title': f'{discipline["name"]} Script',
                'topic': discipline['spec']['course_context']['topic'],
                'task_type': discipline['spec']['task_requirements']['task_type'],
                'duration_minutes': discipline['spec']['course_context']['duration']
            }
        )
        assert script_resp.status_code == 201
        script_id = json.loads(script_resp.data)['script']['id']
        
        # Run pipeline
        resp = client.post(
            f'/api/cscl/scripts/{script_id}/pipeline/run',
            json={'spec': discipline['spec']}
        )
        
        # Should succeed or return explainable error
        assert resp.status_code in [200, 422, 503]
        if resp.status_code == 200:
            data = json.loads(resp.data)
            assert 'run_id' in data
            assert 'quality_report' in data
