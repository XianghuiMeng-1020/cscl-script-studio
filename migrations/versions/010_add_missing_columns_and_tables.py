"""add missing columns and tables

Revision ID: 010
Revises: 009
Create Date: 2026-03-17 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column already exists (handles repeated runs / create_all overlap)."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns(table)]
    return column in cols


def _table_exists(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def upgrade() -> None:
    # --- cscl_scripts: add published_at, share_code ---
    if not _column_exists('cscl_scripts', 'published_at'):
        op.add_column('cscl_scripts', sa.Column('published_at', sa.DateTime(), nullable=True))

    if not _column_exists('cscl_scripts', 'share_code'):
        op.add_column('cscl_scripts', sa.Column('share_code', sa.String(12), nullable=True))
        op.create_index('ix_cscl_scripts_share_code', 'cscl_scripts', ['share_code'], unique=True)

    # --- student_groups ---
    if not _table_exists('student_groups'):
        op.create_table(
            'student_groups',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('script_id', sa.String(36), sa.ForeignKey('cscl_scripts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('group_name', sa.String(200), nullable=False, server_default='Group'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # --- student_group_members ---
    if not _table_exists('student_group_members'):
        op.create_table(
            'student_group_members',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('group_id', sa.String(36), sa.ForeignKey('student_groups.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role_label', sa.String(100), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=False),
        )

    # --- group_messages ---
    if not _table_exists('group_messages'):
        op.create_table(
            'group_messages',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('group_id', sa.String(36), sa.ForeignKey('student_groups.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # --- student_task_submissions ---
    if not _table_exists('student_task_submissions'):
        op.create_table(
            'student_task_submissions',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('script_id', sa.String(36), sa.ForeignKey('cscl_scripts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('scene_id', sa.String(36), sa.ForeignKey('cscl_scenes.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # --- cscl_course_documents: unique constraint on (course_id, checksum) ---
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_uqs = [c['name'] for c in insp.get_unique_constraints('cscl_course_documents')]
    if 'uq_cscl_course_doc_course_checksum' not in existing_uqs:
        try:
            op.create_unique_constraint(
                'uq_cscl_course_doc_course_checksum',
                'cscl_course_documents',
                ['course_id', 'checksum'],
            )
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table('student_task_submissions')
    op.drop_table('group_messages')
    op.drop_table('student_group_members')
    op.drop_table('student_groups')

    op.drop_index('ix_cscl_scripts_share_code', table_name='cscl_scripts')
    op.drop_column('cscl_scripts', 'share_code')
    op.drop_column('cscl_scripts', 'published_at')

    try:
        op.drop_constraint('uq_cscl_course_doc_course_checksum', 'cscl_course_documents', type_='unique')
    except Exception:
        pass
