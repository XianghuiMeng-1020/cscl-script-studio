"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2025-02-05 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('role', sa.Enum('teacher', 'student', 'admin', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create rubrics table
    op.create_table(
        'rubrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('course_id', sa.String(100), nullable=True),
        sa.Column('due_date', sa.String(50), nullable=True),
        sa.Column('rubric_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('assignment_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), nullable=False),
        sa.Column('student_name', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'graded', name='submissionstatus'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('graded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
    )
    
    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('submission_id', sa.String(36), nullable=False),
        sa.Column('rubric_scores', sa.Text(), nullable=True),  # JSON stored as TEXT for compatibility
        sa.Column('written_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id']),
    )
    
    # For PostgreSQL, convert rubric_scores to JSONB if needed
    # This will be handled by the JSON TypeDecorator in models.py


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('feedback')
    op.drop_table('submissions')
    op.drop_table('assignments')
    op.drop_table('rubrics')
    op.drop_table('users')
    
    # Drop enums (PostgreSQL only, SQLite doesn't support DROP TYPE)
    from alembic import context
    bind = context.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS submissionstatus')
        op.execute('DROP TYPE IF EXISTS userrole')
