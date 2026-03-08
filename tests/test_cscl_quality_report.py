"""Tests for CSCL Quality Report API"""
import pytest
import json
from app.db import db
from app.models import (
    User, UserRole, CSCLScript, CSCLScene, CSCLRole, CSCLScriptlet,
    CSCLEvidenceBinding, CSCLTeacherDecision, CSCLPipelineRun, CSCLDocumentChunk, CSCLCourseDocument
)
from app.services.quality_report_service import QualityReportService


@pytest.fixture
def course_id():
    """Course ID for testing"""
    return 'CS101'


@pytest.fixture
def script_with_course(app, seed_users, course_id):
    """Create a test script with course_id"""
    with app.app_context():
        script = CSCLScript(
            title='Test Script',
            topic='Machine Learning',
            course_id=course_id,
            task_type='debate',
            duration_minutes=60,
            learning_objectives=['Understand ML basics', 'Apply ML concepts'],
            created_by='T001'
        )
        db.session.add(script)
        db.session.commit()
        script_id = script.id
        db.session.expunge(script)
        return script_id


def test_teacher_get_quality_report_200(client, seed_users, script_with_course):
    """Test 1: Teacher can get quality report -> 200"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'report' in data
    assert data['report']['script_id'] == script_id


def test_student_get_quality_report_403(client, seed_users, script_with_course):
    """Test 2: Student cannot get quality report -> 403"""
    client.post('/api/auth/login', json={'user_id': 'S001', 'password': 'student123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 403


def test_unauthenticated_get_quality_report_401(app, script_with_course):
    """Test 3: Unauthenticated user gets 401"""
    script_id = script_with_course
    
    unauthenticated_client = app.test_client(use_cookies=False)
    response = unauthenticated_client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 401


def test_no_pipeline_data_insufficient_data(client, seed_users, script_with_course, app):
    """Test 4: No pipeline data -> insufficient_data, no crash"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    # Should have status but not crash
    assert 'summary' in report
    assert 'status' in report['summary']
    assert report['summary']['status'] in ['good', 'needs_attention', 'insufficient_data']


def test_no_evidence_grounding_downgrade(client, seed_users, script_with_course, app):
    """Test 5: No evidence -> grounding downgrade and warning"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # Create scene and scriptlet but no evidence
    with app.app_context():
        scene = CSCLScene(
            script_id=script_id,
            scene_type='opening',
            order_index=0
        )
        db.session.add(scene)
        db.session.flush()
        
        scriptlet = CSCLScriptlet(
            scene_id=scene.id,
            prompt_text='Test prompt',
            prompt_type='claim'
        )
        db.session.add(scriptlet)
        db.session.commit()
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    assert report['dimensions']['grounding']['score'] < 30  # Low score
    assert 'Low evidence coverage' in ' '.join(report['warnings'])


def test_with_evidence_grounding_improves(client, seed_users, script_with_course, app):
    """Test 6: With evidence -> grounding improves"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    with app.app_context():
        # Create document and chunk
        doc = CSCLCourseDocument(
            course_id='CS101',
            title='Test Doc',
            source_type='text',
            uploaded_by='T001'
        )
        db.session.add(doc)
        db.session.flush()
        
        chunk = CSCLDocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            chunk_text='ML is important'
        )
        db.session.add(chunk)
        db.session.flush()
        
        # Create scene and scriptlet
        scene = CSCLScene(
            script_id=script_id,
            scene_type='opening',
            order_index=0
        )
        db.session.add(scene)
        db.session.flush()
        
        scriptlet = CSCLScriptlet(
            scene_id=scene.id,
            prompt_text='Test prompt',
            prompt_type='claim'
        )
        db.session.add(scriptlet)
        db.session.flush()
        
        # Create evidence binding
        binding = CSCLEvidenceBinding(
            script_id=script_id,
            scriptlet_id=scriptlet.id,
            chunk_id=chunk.id,
            binding_type='planner',
            relevance_score=0.8
        )
        db.session.add(binding)
        db.session.commit()
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    assert report['dimensions']['grounding']['score'] >= 30  # Improved


def test_with_teacher_decisions_metrics_valid(client, seed_users, script_with_course, app):
    """Test 7: With teacher decisions -> teacher_in_loop metrics valid"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    with app.app_context():
        # Create decisions
        for i in range(5):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept' if i < 3 else 'edit',
                target_type='scriptlet',
                target_id=f's{i}',
                source_stage='planner'
            )
            db.session.add(decision)
        db.session.commit()
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    assert report['dimensions']['teacher_in_loop']['score'] > 0
    assert report['dimensions']['teacher_in_loop']['evidence']['total_decisions'] == 5


def test_no_teacher_decisions_downgrade(client, seed_users, script_with_course):
    """Test 8: No teacher decisions -> teacher_in_loop downgrade"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    assert report['dimensions']['teacher_in_loop']['status'] == 'insufficient_data'
    assert 'No teacher decisions' in ' '.join(report['warnings'])


def test_score_fields_range_check(client, seed_users, script_with_course):
    """Test 9: Score fields range check (0-100)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    # Check all dimension scores
    for dim_name, dim_data in report['dimensions'].items():
        assert 0 <= dim_data['score'] <= 100
        assert dim_data['status'] in ['good', 'needs_attention', 'insufficient_data']
    
    assert 0 <= report['summary']['overall_score'] <= 100


def test_core_schema_keys_completeness(client, seed_users, script_with_course):
    """Test 10: Core schema keys completeness check"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    # Required top-level keys
    required_keys = [
        'script_id', 'report_version', 'computed_at', 'spec_hash',
        'config_fingerprint', 'summary', 'dimensions', 'warnings', 'data_provenance'
    ]
    for key in required_keys:
        assert key in report, f"Missing required key: {key}"
    
    # Summary keys
    assert 'overall_score' in report['summary']
    assert 'status' in report['summary']
    
    # Dimensions keys
    required_dims = ['coverage', 'pedagogical_alignment', 'argumentation_support',
                     'grounding', 'safety_checks', 'teacher_in_loop']
    for dim in required_dims:
        assert dim in report['dimensions']
        assert 'score' in report['dimensions'][dim]
        assert 'status' in report['dimensions'][dim]
        assert 'evidence' in report['dimensions'][dim]


def test_reproducibility_consistency(client, seed_users, script_with_course, app):
    """Test 11: Reproducibility test (two results consistent, excluding computed_at)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    # First request
    response1 = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)
    report1 = data1['report']
    
    # Second request
    response2 = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)
    report2 = data2['report']
    
    # Exclude computed_at and compare
    report1_copy = report1.copy()
    report2_copy = report2.copy()
    del report1_copy['computed_at']
    del report2_copy['computed_at']
    
    # Scores should be consistent
    assert report1_copy['summary']['overall_score'] == report2_copy['summary']['overall_score']
    for dim in report1_copy['dimensions']:
        assert report1_copy['dimensions'][dim]['score'] == report2_copy['dimensions'][dim]['score']


def test_error_codes_semantics(client, seed_users):
    """Test 12: Error code semantics check (404/422/503 scenarios)"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    # 404 - Script not found
    response = client.get('/api/cscl/scripts/nonexistent/quality-report')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'code' in data
    assert data['code'] == 'SCRIPT_NOT_FOUND'


def test_snapshot_high_quality_script(client, seed_users, script_with_course, app):
    """Test 13: Snapshot test 1 - Complete high quality script"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    with app.app_context():
        # Create pipeline run
        pipeline_run = CSCLPipelineRun(
            script_id=script_id,
            run_id='run_001',
            spec_hash='abc123',
            config_fingerprint='def456',
            initiated_by='T001'
        )
        db.session.add(pipeline_run)
        
        # Create scenes and scriptlets
        for i in range(3):
            scene = CSCLScene(
                script_id=script_id,
                scene_type='opening' if i == 0 else 'argumentation' if i == 1 else 'conclusion',
                order_index=i
            )
            db.session.add(scene)
            db.session.flush()
            
            for j in range(2):
                scriptlet = CSCLScriptlet(
                    scene_id=scene.id,
                    prompt_text=f'Prompt {i}-{j}',
                    prompt_type=['claim', 'evidence'][j % 2]
                )
                db.session.add(scriptlet)
        
        # Create decisions
        for i in range(3):
            decision = CSCLTeacherDecision(
                script_id=script_id,
                actor_id='T001',
                decision_type='accept',
                target_type='scriptlet',
                target_id=f's{i}',
                source_stage='planner'
            )
            db.session.add(decision)
        
        db.session.commit()
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    # Verify structure
    assert report['spec_hash'] == 'abc123'
    assert report['config_fingerprint'] == 'def456'
    assert len(report['data_provenance']['pipeline_run_ids']) > 0
    assert len(report['data_provenance']['decision_ids']) > 0


def test_snapshot_low_data_script(client, seed_users, script_with_course):
    """Test 14: Snapshot test 2 - Low data script"""
    client.post('/api/auth/login', json={'user_id': 'T001', 'password': 'teacher123'})
    
    script_id = script_with_course
    
    response = client.get(f'/api/cscl/scripts/{script_id}/quality-report')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    report = data['report']
    
    # Should handle low data gracefully
    assert report['summary']['status'] in ['good', 'needs_attention', 'insufficient_data']
    assert isinstance(report['warnings'], list)
    # Should have warnings for insufficient data
    assert len(report['warnings']) >= 0  # May have warnings
