"""add file_data column to store file binary in database

Revision ID: 012
Revises: 011
Create Date: 2026-03-31 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c['name'] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _column_exists('cscl_course_documents', 'file_data'):
        op.add_column(
            'cscl_course_documents',
            sa.Column('file_data', sa.LargeBinary(), nullable=True)
        )


def downgrade() -> None:
    if _column_exists('cscl_course_documents', 'file_data'):
        op.drop_column('cscl_course_documents', 'file_data')
