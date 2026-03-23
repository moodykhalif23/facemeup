"""add_product_effects

Revision ID: 0004_add_product_effects
Revises: 0003_add_product_fields
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_add_product_effects'
down_revision: Union[str, None] = '0003_add_product_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'product_catalog',
        sa.Column('suitable_for', sa.String(length=16), nullable=False, server_default='all'),
    )
    op.add_column(
        'product_catalog',
        sa.Column('effects_csv', sa.String(length=1024), nullable=False, server_default=''),
    )
    op.alter_column('product_catalog', 'suitable_for', server_default=None)
    op.alter_column('product_catalog', 'effects_csv', server_default=None)


def downgrade() -> None:
    op.drop_column('product_catalog', 'effects_csv')
    op.drop_column('product_catalog', 'suitable_for')
