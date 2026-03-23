"""add_report_thumbnail

Revision ID: 0006_add_report_thumbnail
Revises: 0005_add_profile_report_fields
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_add_report_thumbnail'
down_revision: Union[str, None] = '0005_add_profile_report_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('skin_profile_history', sa.Column('report_image_base64', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('skin_profile_history', 'report_image_base64')
