"""add_profile_report_fields

Revision ID: 0005_add_profile_report_fields
Revises: 0004_add_product_effects
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_add_profile_report_fields'
down_revision: Union[str, None] = '0004_add_product_effects'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('skin_profile_history', sa.Column('questionnaire_json', sa.Text(), nullable=True))
    op.add_column('skin_profile_history', sa.Column('skin_type_scores_json', sa.Text(), nullable=True))
    op.add_column('skin_profile_history', sa.Column('condition_scores_json', sa.Text(), nullable=True))
    op.add_column('skin_profile_history', sa.Column('inference_mode', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('skin_profile_history', 'inference_mode')
    op.drop_column('skin_profile_history', 'condition_scores_json')
    op.drop_column('skin_profile_history', 'skin_type_scores_json')
    op.drop_column('skin_profile_history', 'questionnaire_json')
