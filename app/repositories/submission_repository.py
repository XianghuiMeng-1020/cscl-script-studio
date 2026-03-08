"""Submission repository - DB and JSON implementations"""
from abc import ABC, abstractmethod
from app.db import db
from app.models import Submission, SubmissionStatus, Feedback
from app.config import Config
from app.utils import load_json, save_json
from datetime import datetime


class SubmissionRepository(ABC):
    """Abstract submission repository"""
    
    @abstractmethod
    def get_all(self, assignment_id=None, student_id=None, status=None):
        """Get all submissions with optional filtering"""
        pass
    
    @abstractmethod
    def get_by_id(self, submission_id):
        """Get submission by ID"""
        pass
    
    @abstractmethod
    def create(self, submission_data):
        """Create new submission"""
        pass
    
    @abstractmethod
    def delete_all(self):
        """Delete all submissions (for demo init idempotency)"""
        pass


class DBSubmissionRepository(SubmissionRepository):
    """Database-backed submission repository"""
    
    def get_all(self, assignment_id=None, student_id=None, status=None):
        """Get all submissions from DB with optional filtering"""
        query = Submission.query
        
        if assignment_id:
            query = query.filter_by(assignment_id=assignment_id)
        if student_id:
            query = query.filter_by(student_id=student_id)
        if status:
            status_enum = SubmissionStatus.PENDING if status == 'pending' else SubmissionStatus.GRADED
            query = query.filter_by(status=status_enum)
        
        submissions = query.all()
        result = []
        for s in submissions:
            sub_dict = s.to_dict()
            # Load feedback data if exists
            feedback = Feedback.query.filter_by(submission_id=s.id).first()
            if feedback:
                sub_dict['feedback'] = feedback.written_feedback
                sub_dict['rubric_scores'] = feedback.rubric_scores
            result.append(sub_dict)
        return result
    
    def get_by_id(self, submission_id):
        """Get submission by ID from DB"""
        submission = Submission.query.filter_by(id=submission_id).first()
        if not submission:
            return None
        sub_dict = submission.to_dict()
        # Load feedback data if exists
        feedback = Feedback.query.filter_by(submission_id=submission_id).first()
        if feedback:
            sub_dict['feedback'] = feedback.written_feedback
            sub_dict['rubric_scores'] = feedback.rubric_scores
        return sub_dict
    
    def create(self, submission_data):
        """Create submission in DB"""
        submitted_at = None
        if submission_data.get('submitted_at'):
            try:
                submitted_at = datetime.fromisoformat(submission_data['submitted_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                submitted_at = datetime.utcnow()
        else:
            submitted_at = datetime.utcnow()
        
        created_at = submitted_at  # Use submitted_at as created_at if available
        
        submission = Submission(
            id=submission_data.get('id'),
            assignment_id=submission_data.get('assignment_id', ''),
            student_id=submission_data.get('student_id', ''),
            student_name=submission_data.get('student_name'),
            content=submission_data.get('content', ''),
            status=SubmissionStatus.PENDING if submission_data.get('status') == 'pending' else SubmissionStatus.GRADED,
            submitted_at=submitted_at,
            created_at=created_at
        )
        db.session.add(submission)
        db.session.commit()
        return submission.to_dict()
    
    def delete_all(self):
        """Delete all submissions (for demo init idempotency)"""
        Submission.query.delete()
        db.session.commit()


class JsonSubmissionRepository(SubmissionRepository):
    """JSON file-backed submission repository"""
    
    def get_all(self, assignment_id=None, student_id=None, status=None):
        """Get all submissions from JSON file with optional filtering"""
        submissions = load_json(Config.SUBMISSIONS_FILE)
        
        if assignment_id:
            submissions = [s for s in submissions if s.get('assignment_id') == assignment_id]
        if student_id:
            submissions = [s for s in submissions if s.get('student_id') == student_id]
        if status:
            submissions = [s for s in submissions if s.get('status') == status]
        
        return submissions
    
    def get_by_id(self, submission_id):
        """Get submission by ID from JSON file"""
        submissions = load_json(Config.SUBMISSIONS_FILE)
        return next((s for s in submissions if s.get('id') == submission_id), None)
    
    def create(self, submission_data):
        """Create submission in JSON file"""
        submissions = load_json(Config.SUBMISSIONS_FILE)
        submissions.append(submission_data)
        save_json(Config.SUBMISSIONS_FILE, submissions)
        return submission_data
    
    def delete_all(self):
        """Delete all submissions (clear JSON file)"""
        save_json(Config.SUBMISSIONS_FILE, [])
