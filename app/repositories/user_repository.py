"""User repository - DB and JSON implementations"""
from abc import ABC, abstractmethod
from app.db import db
from app.models import User, UserRole
from app.config import Config
from app.utils import load_json, save_json
from datetime import datetime


class UserRepository(ABC):
    """Abstract user repository"""
    
    @abstractmethod
    def get_all(self):
        """Get all users"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id):
        """Get user by ID"""
        pass
    
    @abstractmethod
    def create(self, user_data):
        """Create new user"""
        pass
    
    @abstractmethod
    def delete_all(self):
        """Delete all users (for demo init idempotency)"""
        pass


class DBUserRepository(UserRepository):
    """Database-backed user repository"""
    
    def get_all(self):
        """Get all users from DB"""
        users = User.query.all()
        return [u.to_dict() for u in users]
    
    def get_by_id(self, user_id):
        """Get user by ID from DB"""
        user = User.query.filter_by(id=user_id).first()
        return user.to_dict() if user else None
    
    def create(self, user_data):
        """Create user in DB"""
        role_str = user_data.get('role', 'student')
        role = UserRole.STUDENT if role_str == 'student' else (UserRole.TEACHER if role_str == 'teacher' else UserRole.ADMIN)
        
        created_at = datetime.utcnow()
        if user_data.get('created_at'):
            try:
                created_at = datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.utcnow()
        
        user = User(
            id=user_data.get('id'),
            role=role,
            created_at=created_at
        )
        db.session.add(user)
        db.session.commit()
        return user.to_dict()
    
    def delete_all(self):
        """Delete all users (for demo init idempotency)"""
        User.query.delete()
        db.session.commit()


class JsonUserRepository(UserRepository):
    """JSON file-backed user repository"""
    
    def get_all(self):
        """Get all users from JSON file"""
        return load_json(Config.USERS_FILE)
    
    def get_by_id(self, user_id):
        """Get user by ID from JSON file"""
        users_data = load_json(Config.USERS_FILE)
        if isinstance(users_data, dict):
            # Check in teachers and students
            for teacher in users_data.get('teachers', []):
                if teacher.get('id') == user_id:
                    return teacher
            for student in users_data.get('students', []):
                if student.get('id') == user_id:
                    return student
        return None
    
    def create(self, user_data):
        """Create user in JSON file (not used for JSON mode, users are in USERS_FILE)"""
        # JSON mode uses USERS_FILE structure, so this is a no-op
        pass
    
    def delete_all(self):
        """Delete all users (clear JSON file)"""
        save_json(Config.USERS_FILE, {"teachers": [], "students": []})
