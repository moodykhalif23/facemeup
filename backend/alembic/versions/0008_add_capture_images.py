"""add_capture_images

Revision ID: 0008_add_capture_images
Revises: 0007_add_profile_user_feedback
Create Date: 2026-04-07

Adds capture_images_json column to skin_profile_history to store all
pose captures (up to 5) submitted during an analysis session.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0008_add_capture_images'
down_revision: Union[str, None] = '0007_add_profile_user_feedback'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'skin_profile_history',
        sa.Column('capture_images_json', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('skin_profile_history', 'capture_images_json')
