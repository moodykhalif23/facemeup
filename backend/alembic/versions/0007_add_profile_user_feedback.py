"""add_profile_user_feedback

Revision ID: 0007_add_profile_user_feedback
Revises: 0006_add_report_thumbnail
Create Date: 2026-04-06

Adds user_feedback column to skin_profile_history for the continuous
learning feedback loop (spec §9): stores "confirmed" | "rejected" | NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007_add_profile_user_feedback'
down_revision: Union[str, None] = '0006_add_report_thumbnail'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'skin_profile_history',
        sa.Column('user_feedback', sa.String(16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('skin_profile_history', 'user_feedback')
