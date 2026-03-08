"""Snapshot tests for decision export format stability"""
import pytest
import json
from app import create_app
from app.db import db
from app.models import User, UserRole, CSCLScript, CSCLTeacherDecision
from app.services.decision_summary_service import DecisionSummaryService
from datetime import datetime


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['USE_DB_STORAGE'] = True
    app.config['DATABASE_URL'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def seed_teacher(app):
    """Create teacher user T001 so script FK can reference it"""
    with app.app_context():
        user = User(id='T001', role=UserRole.TEACHER)
        user.set_password('teacher123')
        db.session.add(user)
        db.session.commit()
        yield user


@pytest.fixture
def script_id(app, seed_teacher):
    """Create test script"""
    with app.app_context():
        script = CSCLScript(
            id='script001',
            title='Test Script',
            topic='ML',
            task_type='debate',
            duration_minutes=60,
            created_by='T001'
        )
        db.session.add(script)
        db.session.commit()
        return script.id


def test_export_schema_structure(app, script_id):
    """Test export JSON has required fields with correct types"""
    with app.app_context():
        timeline = DecisionSummaryService.get_timeline(script_id)
        summary = DecisionSummaryService.compute_summary(script_id)
        
        export_data = {
            'schema_version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'script_id': script_id,
            'spec_hash': None,
            'config_fingerprint': None,
            'timeline': timeline,
            'summary': summary
        }
        
        # Verify required fields exist
        assert 'schema_version' in export_data
        assert 'generated_at' in export_data
        assert 'script_id' in export_data
        assert 'spec_hash' in export_data
        assert 'config_fingerprint' in export_data
        assert 'timeline' in export_data
        assert 'summary' in export_data
        
        # Verify field types
        assert isinstance(export_data['schema_version'], str)
        assert isinstance(export_data['generated_at'], str)
        assert isinstance(export_data['script_id'], str)
        assert export_data['spec_hash'] is None or isinstance(export_data['spec_hash'], str)
        assert export_data['config_fingerprint'] is None or isinstance(export_data['config_fingerprint'], str)
        assert isinstance(export_data['timeline'], list)
        assert isinstance(export_data['summary'], dict)
        
        # Verify schema_version format
        assert export_data['schema_version'].count('.') == 2  # e.g., "1.0.0"


def test_summary_structure_stability(app, script_id):
    """Test summary structure has all required fields"""
    with app.app_context():
        summary = DecisionSummaryService.compute_summary(script_id)
        
        # Required fields
        required_fields = [
            'total_decisions',
            'accept_rate',
            'reject_rate',
            'edit_rate',
            'stage_adoption_rate',
            'avg_time_to_finalize',
            'evidence_linked_edit_rate',
            'top_modified_target_types',
            'decision_count_by_stage',
            'decision_count_by_target_type',
            'reproducibility'
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"
        
        # Verify types
        assert isinstance(summary['total_decisions'], int)
        assert isinstance(summary['accept_rate'], float)
        assert isinstance(summary['reject_rate'], float)
        assert isinstance(summary['edit_rate'], float)
        assert isinstance(summary['stage_adoption_rate'], dict)
        assert summary['avg_time_to_finalize'] is None or isinstance(summary['avg_time_to_finalize'], float)
        assert isinstance(summary['evidence_linked_edit_rate'], float)
        assert isinstance(summary['top_modified_target_types'], list)
        assert isinstance(summary['decision_count_by_stage'], dict)
        assert isinstance(summary['decision_count_by_target_type'], dict)
        assert isinstance(summary['reproducibility'], dict)


def test_empty_decisions_export_stability(app, script_id):
    """Test export format is stable even with no decisions"""
    with app.app_context():
        timeline = DecisionSummaryService.get_timeline(script_id)
        summary = DecisionSummaryService.compute_summary(script_id)
        
        export_data = {
            'schema_version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'script_id': script_id,
            'spec_hash': None,
            'config_fingerprint': None,
            'timeline': timeline,
            'summary': summary
        }
        
        # Verify empty state
        assert export_data['timeline'] == []
        assert export_data['summary']['total_decisions'] == 0
        assert export_data['summary']['decision_count_by_stage'] == {}
        assert export_data['summary']['decision_count_by_target_type'] == {}
        
        # Verify JSON serialization
        json_str = json.dumps(export_data, default=str)
        assert json_str is not None
        parsed = json.loads(json_str)
        assert parsed['schema_version'] == '1.0.0'


def test_timeline_item_structure(app, script_id):
    """Test timeline items have consistent structure"""
    with app.app_context():
        # Create a decision
        decision = CSCLTeacherDecision(
            script_id=script_id,
            actor_id='T001',
            decision_type='accept',
            target_type='scriptlet',
            target_id='s1',
            source_stage='planner'
        )
        db.session.add(decision)
        db.session.commit()
        
        timeline = DecisionSummaryService.get_timeline(script_id)
        
        assert len(timeline) == 1
        item = timeline[0]
        
        # Required fields
        required_fields = [
            'id',
            'script_id',
            'revision_id',
            'actor_id',
            'decision_type',
            'target_type',
            'target_id',
            'before_json',
            'after_json',
            'rationale_text',
            'source_stage',
            'confidence',
            'created_at'
        ]
        
        for field in required_fields:
            assert field in item, f"Missing required field in timeline item: {field}"
