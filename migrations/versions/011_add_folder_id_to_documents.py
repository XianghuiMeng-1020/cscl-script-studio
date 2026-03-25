"""add folder_id column to cscl_course_documents

Revision ID: 011
Revises: 010
Create Date: 2026-03-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _column_exists('cscl_course_documents', 'folder_id'):
        op.add_column(
            'cscl_course_documents',
            sa.Column('folder_id', sa.String(36), sa.ForeignKey('cscl_course_folders.id'), nullable=True)
        )


def downgrade() -> None:
    if _column_exists('cscl_course_documents', 'folder_id'):
        op.drop_column('cscl_course_documents', 'folder_id')
