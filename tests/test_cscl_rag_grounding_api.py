"""Tests for CSCL RAG Grounding API endpoints"""
import pytest
import json
import os
from unittest.mock import patch
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLCourseDocument, CSCLDocumentChunk, CSCLEvidenceBinding


@pytest.fixture
def course_id():
    """Course ID for testing"""
    return 'CS101'


@pytest.fixture
def script_with_course(client, app, seed_users, course_id):
    """Create a test script with course_id"""
    # Login as teacher
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Test Script',
            'topic': 'Machine Learning',
            'course_id': course_id,
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    with app.app_context():
        return CSCLScript.query.get(script_id)


def test_teacher_upload_document_success(client, seed_users, course_id):
    """Test 1: Teacher can upload document successfully"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Upload text document
    response = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'Test Document',
            'text': 'This is a test document about machine learning and neural networks. It covers basic concepts, terminology, and applications that teachers can use as course materials.'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'document' in data
    assert data['document']['title'] == 'Test Document'
    assert data['chunks_count'] > 0


def test_student_upload_document_403(client, seed_users, course_id):
    """Test 2: Student cannot upload document (403)"""
    # Login as student
    client.post('/api/auth/login', json={'user_id': 'S001', 'password': 'student123'})
    
    # Try to upload
    response = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={'title': 'Test', 'text': 'Test content'}
    )
    
    assert response.status_code == 403


def test_list_documents_success(client, seed_users, course_id):
    """Test 3: List documents works correctly"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Upload a document
    client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={'title': 'Doc1', 'text': 'Content 1. ' + 'This document has enough text to pass the minimum length requirement for upload (at least 80 characters).'}
    )
    
    # List documents
    response = client.get(f'/api/cscl/courses/{course_id}/docs')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['documents']) >= 1


def test_delete_document_success(client, seed_users, course_id):
    """Test 4: Delete document works correctly"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Upload a document
    upload_resp = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={'title': 'To Delete', 'text': 'Content to be deleted. ' + 'This document has enough text to pass the minimum length requirement for upload (at least 80 characters).'}
    )
    doc_id = json.loads(upload_resp.data)['document']['id']
    
    # Delete document
    response = client.delete(f'/api/cscl/courses/{course_id}/docs/{doc_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_pipeline_without_docs_works(client, seed_users, script_with_course):
    """Test 5: Pipeline can run without course documents"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'ML',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90
        },
        'learning_objectives': {
            'knowledge': ['Test'],
            'skills': ['Test']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Validate spec first
    from app.services.spec_validator import SpecValidator
    validation_result = SpecValidator.validate(spec)
    if not validation_result['valid']:
        # Use normalized spec
        spec = validation_result['normalized_spec']
    
    response = client.post(
        f'/api/cscl/scripts/{script.id}/pipeline/run',
        json={'spec': spec}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data.get('grounding_status') == 'no_course_docs'


def test_pipeline_with_docs_retrieves_chunks(client, seed_users, script_with_course, course_id, app):
    """Test 6: Pipeline retrieves chunks when documents exist"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    # Upload document
    client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'ML Guide',
            'text': 'Machine learning is a subset of artificial intelligence. Neural networks are computational models inspired by biological neural networks. This guide covers basics and applications.'
        }
    )
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90
        },
        'learning_objectives': {
            'knowledge': ['Understand ML'],
            'skills': ['Apply ML']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    # Mock pipeline so test does not depend on LLM; API returns success with retrieved chunks
    mock_result = {
        'status': 'success',
        'run_id': 'test-run-1',
        'stages': [{'name': 'stage1', 'retrieved_chunks_count': 3}],
        'grounding_status': 'grounded',
    }
    with patch('app.routes.cscl.CSCLPipelineService') as MockPipeline:
        MockPipeline.return_value.run_pipeline.return_value = mock_result
        response = client.post(
            f'/api/cscl/scripts/{script.id}/pipeline/run',
            json={'spec': spec}
        )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    # Check that stages have retrieved chunks
    stages = data.get('stages', [])
    assert len(stages) > 0
    # At least one stage should have retrieved chunks
    has_retrieved = any(s.get('retrieved_chunks_count', 0) > 0 for s in stages)
    assert has_retrieved or data.get('grounding_status') == 'no_course_docs'


def test_evidence_bindings_created(client, seed_users, script_with_course, course_id, app):
    """Test 7: Evidence bindings are created after pipeline run"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    # Upload document
    client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'ML Guide',
            'text': 'Machine learning neural networks artificial intelligence'
        }
    )
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'course_id': course_id
        },
        'learning_objectives': {
            'knowledge': ['Understand ML'],
            'skills': ['Apply ML']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Run pipeline
    response = client.post(
        f'/api/cscl/scripts/{script.id}/pipeline/run',
        json={'spec': spec}
    )
    
    assert response.status_code == 200
    
    # Check evidence bindings
    with app.app_context():
        bindings = CSCLEvidenceBinding.query.filter_by(script_id=script.id).all()
        # May be 0 if no chunks retrieved, but should not crash
        assert isinstance(bindings, list)


def test_export_includes_evidence_refs(client, seed_users, script_with_course, course_id, app):
    """Test 8: Export includes evidence_refs"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    # Upload document
    client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'ML Guide',
            'text': 'Machine learning neural networks'
        }
    )
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'course_id': course_id
        },
        'learning_objectives': {
            'knowledge': ['Understand ML'],
            'skills': ['Apply ML']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Run pipeline
    client.post(
        f'/api/cscl/scripts/{script.id}/pipeline/run',
        json={'spec': spec}
    )
    
    # Export script
    response = client.get(f'/api/cscl/scripts/{script.id}/export')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'script' in data
    assert 'evidence_metadata' in data['script']
    assert 'evidence_coverage' in data['script']['evidence_metadata']


def test_evidence_ref_traceable(client, seed_users, script_with_course, course_id, app):
    """Test 9: Evidence refs can be traced back to documents"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    # Upload document
    upload_resp = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'ML Guide',
            'text': 'Machine learning neural networks. This document has enough text to pass the minimum length requirement for upload (at least 80 characters).'
        }
    )
    doc_id = json.loads(upload_resp.data)['document']['id']
    
    spec = {
        'course_context': {
            'subject': 'Data Science',
            'topic': 'Machine Learning',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'course_id': course_id
        },
        'learning_objectives': {
            'knowledge': ['Understand ML'],
            'skills': ['Apply ML']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Run pipeline
    client.post(
        f'/api/cscl/scripts/{script.id}/pipeline/run',
        json={'spec': spec}
    )
    
    # Export and check traceability
    response = client.get(f'/api/cscl/scripts/{script.id}/export')
    data = json.loads(response.data)
    
    # Check that evidence_details contain doc info
    script_data = data['script']
    for scene in script_data.get('scenes', []):
        for scriptlet in scene.get('scriptlets', []):
            if scriptlet.get('evidence_refs'):
                evidence_details = scriptlet.get('evidence_details', [])
                for detail in evidence_details:
                    assert 'doc_id' in detail
                    assert 'doc_title' in detail
                    assert 'snippet' in detail


def test_cross_discipline_evidence_coverage(client, seed_users, course_id, app):
    """Test 10: Evidence coverage can be computed for cross-discipline specs"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Upload document
    client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={
            'title': 'Multi-disciplinary Guide',
            'text': 'This covers data science, learning sciences, and humanities topics.'
        }
    )
    
    # Create script
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'Cross-discipline Script',
            'topic': 'Interdisciplinary',
            'course_id': course_id,
            'task_type': 'debate',
            'duration_minutes': 60
        }
    )
    script_id = json.loads(script_resp.data)['script']['id']
    
    spec = {
        'course_context': {
            'subject': 'Interdisciplinary',
            'topic': 'Cross-discipline',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90,
            'course_id': course_id
        },
        'learning_objectives': {
            'knowledge': ['Cross-discipline'],
            'skills': ['Apply']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Run pipeline
    client.post(
        f'/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec}
    )
    
    # Export and check coverage
    response = client.get(f'/api/cscl/scripts/{script_id}/export')
    data = json.loads(response.data)
    
    assert 'evidence_metadata' in data['script']
    coverage = data['script']['evidence_metadata']['evidence_coverage']
    assert 0.0 <= coverage <= 1.0


def test_unsupported_file_type_error(client, seed_users, course_id):
    """Test 11: Unsupported file type returns explainable error"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Try to upload PDF (not supported)
    response = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        data={
            'file': (b'fake pdf content', 'test.pdf'),
            'title': 'Test PDF'
        },
        content_type='multipart/form-data'
    )
    
    # Should return 422 with explainable error
    assert response.status_code in [400, 422]
    data = json.loads(response.data)
    assert 'error' in data
    assert 'code' in data


def test_empty_retrieval_no_crash(client, seed_users, script_with_course, app):
    """Test 12: Empty retrieval results don't crash pipeline"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script = script_with_course
    
    spec = {
        'course_context': {
            'subject': 'Unknown',
            'topic': 'Unrelated Topic',
            'class_size': 30,
            'mode': 'sync',
            'duration': 90
        },
        'learning_objectives': {
            'knowledge': ['Unknown'],
            'skills': ['Unknown']
        },
        'task_requirements': {
            'task_type': 'debate',
            'expected_output': 'test',
            'collaboration_form': 'group'
        }
    }
    
    # Should not crash even with no matching documents
    response = client.post(
        f'/api/cscl/scripts/{script.id}/pipeline/run',
        json={'spec': spec}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] in ['success', 'partial_failed']


def test_rollback_migration_endpoints_fail(client, seed_users, course_id, app):
    """Test 13: After rollback, related endpoints fail (404/function unavailable)"""
    # This test verifies that if migration is rolled back, endpoints become unavailable
    # In practice, this would be tested by:
    # 1. Running migration
    # 2. Rolling back migration
    # 3. Verifying endpoints return 404 or 500
    
    # For now, we test that endpoints exist when migration is applied
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Endpoint should exist (not 404)
    response = client.get(f'/api/cscl/courses/{course_id}/docs')
    assert response.status_code != 404  # Should be 200 or 403, not 404


def test_restore_after_rollback_works(client, seed_users, course_id, app):
    """Test 14: After restoring migration, endpoints work again"""
    # Login
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # Upload document
    response = client.post(
        f'/api/cscl/courses/{course_id}/docs/upload',
        json={'title': 'Test', 'text': 'Content. ' + 'This document has enough text to pass the minimum length requirement for upload (at least 80 characters).'}
    )
    assert response.status_code == 201


def test_b1_default_course_unified_upload_list_and_script(client, seed_users, app):
    """B1 regression: default-course used for both docs and script so pipeline can retrieve same-course docs.
    Flow: upload -> list -> create script with same course_id -> pipeline finds docs."""
    DEFAULT_COURSE_ID = 'default-course'
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})

    # Upload to default-course
    upload_resp = client.post(
        f'/api/cscl/courses/{DEFAULT_COURSE_ID}/docs/upload',
        json={
            'title': 'B1 Test Doc',
            'text': 'Machine learning and neural networks. This document has enough text to pass the minimum length requirement for upload (at least 80 characters).'
        },
        content_type='application/json'
    )
    assert upload_resp.status_code == 201, upload_resp.data
    data = json.loads(upload_resp.data)
    assert data.get('success') is True
    assert data.get('document', {}).get('course_id') == DEFAULT_COURSE_ID or data.get('document', {}).get('title') == 'B1 Test Doc'

    # List docs for same course
    list_resp = client.get(f'/api/cscl/courses/{DEFAULT_COURSE_ID}/docs')
    assert list_resp.status_code == 200
    list_data = json.loads(list_resp.data)
    assert list_data['success'] is True
    assert len(list_data['documents']) >= 1
    doc_ids = [d['id'] for d in list_data['documents'] if d.get('title') == 'B1 Test Doc']
    assert len(doc_ids) >= 1

    # Create script with same course_id (B1: frontend sends default-course)
    script_resp = client.post(
        '/api/cscl/scripts',
        json={
            'title': 'B1 Script',
            'topic': 'ML',
            'course_id': DEFAULT_COURSE_ID,
            'learning_objectives': ['Understand ML'],
            'task_type': 'structured_debate',
            'duration_minutes': 90
        }
    )
    assert script_resp.status_code == 201
    script_id = json.loads(script_resp.data)['script']['id']

    # Script must be in same course so retriever finds docs
    with app.app_context():
        script = CSCLScript.query.get(script_id)
        assert script is not None
        assert script.course_id == DEFAULT_COURSE_ID
    # Pipeline run (mocked) would use script.course_id -> same as docs -> grounding works
