"""add_auth_and_audit

Revision ID: 002
Revises: 001
Create Date: 2025-02-05 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add authentication fields to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('token_expires_at', sa.DateTime(), nullable=True))
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('actor_id', sa.String(36), nullable=True),
        sa.Column('role', sa.Enum('teacher', 'student', 'admin', name='userrole'), nullable=True),
        sa.Column('target_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='success'),
        sa.Column('meta_json', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('audit_logs')
    op.drop_column('users', 'token_expires_at')
    op.drop_column('users', 'token')
    op.drop_column('users', 'password_hash')
