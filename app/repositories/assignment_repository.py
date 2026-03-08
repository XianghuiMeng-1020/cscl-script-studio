"""Assignment repository - DB and JSON implementations"""
from abc import ABC, abstractmethod
from app.db import db
from app.models import Assignment
from app.config import Config
from app.utils import load_json, save_json
from datetime import datetime


class AssignmentRepository(ABC):
    """Abstract assignment repository"""
    
    @abstractmethod
    def get_all(self):
        """Get all assignments"""
        pass
    
    @abstractmethod
    def get_by_id(self, assignment_id):
        """Get assignment by ID"""
        pass
    
    @abstractmethod
    def create(self, assignment_data):
        """Create new assignment"""
        pass
    
    @abstractmethod
    def delete_all(self):
        """Delete all assignments (for demo init idempotency)"""
        pass


class DBAssignmentRepository(AssignmentRepository):
    """Database-backed assignment repository"""
    
    def get_all(self):
        """Get all assignments from DB"""
        assignments = Assignment.query.all()
        return [a.to_dict() for a in assignments]
    
    def get_by_id(self, assignment_id):
        """Get assignment by ID from DB"""
        assignment = Assignment.query.filter_by(id=assignment_id).first()
        return assignment.to_dict() if assignment else None
    
    def create(self, assignment_data):
        """Create assignment in DB"""
        created_at = datetime.utcnow()
        if assignment_data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(assignment_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.utcnow()
        
        assignment = Assignment(
            id=assignment_data.get('id'),
            title=assignment_data.get('title', ''),
            description=assignment_data.get('description'),
            course_id=assignment_data.get('course_id'),
            due_date=assignment_data.get('due_date'),
            rubric_id=assignment_data.get('rubric_id'),
            status=assignment_data.get('status', 'active'),
            created_at=created_at
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment.to_dict()
    
    def delete_all(self):
        """Delete all assignments (for demo init idempotency)"""
        Assignment.query.delete()
        db.session.commit()


class JsonAssignmentRepository(AssignmentRepository):
    """JSON file-backed assignment repository"""
    
    def get_all(self):
        """Get all assignments from JSON file"""
        return load_json(Config.ASSIGNMENTS_FILE)
    
    def get_by_id(self, assignment_id):
        """Get assignment by ID from JSON file"""
        assignments = load_json(Config.ASSIGNMENTS_FILE)
        return next((a for a in assignments if a.get('id') == assignment_id), None)
    
    def create(self, assignment_data):
        """Create assignment in JSON file"""
        assignments = load_json(Config.ASSIGNMENTS_FILE)
        assignments.append(assignment_data)
        save_json(Config.ASSIGNMENTS_FILE, assignments)
        return assignment_data
    
    def delete_all(self):
        """Delete all assignments (clear JSON file)"""
        save_json(Config.ASSIGNMENTS_FILE, [])
