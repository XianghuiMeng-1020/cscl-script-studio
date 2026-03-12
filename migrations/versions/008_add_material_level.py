"""add material_level to cscl_course_documents

Revision ID: 008
Revises: 007
Create Date: 2025-03-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'cscl_course_documents',
        sa.Column('material_level', sa.String(20), nullable=False, server_default='course')
    )


def downgrade() -> None:
    op.drop_column('cscl_course_documents', 'material_level')
