"""Repository pattern for data access layer"""
from app.config import Config
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.rubric_repository import RubricRepository
from app.repositories.user_repository import UserRepository


def get_assignment_repo():
    """Get assignment repository based on USE_DB_STORAGE config"""
    if Config.USE_DB_STORAGE:
        from app.repositories.assignment_repository import DBAssignmentRepository
        return DBAssignmentRepository()
    else:
        from app.repositories.assignment_repository import JsonAssignmentRepository
        return JsonAssignmentRepository()


def get_submission_repo():
    """Get submission repository based on USE_DB_STORAGE config"""
    if Config.USE_DB_STORAGE:
        from app.repositories.submission_repository import DBSubmissionRepository
        return DBSubmissionRepository()
    else:
        from app.repositories.submission_repository import JsonSubmissionRepository
        return JsonSubmissionRepository()


def get_rubric_repo():
    """Get rubric repository based on USE_DB_STORAGE config"""
    if Config.USE_DB_STORAGE:
        from app.repositories.rubric_repository import DBRubricRepository
        return DBRubricRepository()
    else:
        from app.repositories.rubric_repository import JsonRubricRepository
        return JsonRubricRepository()


def get_user_repo():
    """Get user repository based on USE_DB_STORAGE config"""
    if Config.USE_DB_STORAGE:
        from app.repositories.user_repository import DBUserRepository
        return DBUserRepository()
    else:
        from app.repositories.user_repository import JsonUserRepository
        return JsonUserRepository()
