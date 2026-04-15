"""Add benefits_csv and usage to product_catalog

Revision ID: 0010_add_product_benefits_usage
Revises: 0009_add_soft_delete
Create Date: 2026-04-15
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = '0010_add_product_benefits_usage'
down_revision: Union[str, None] = '0009_add_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('product_catalog', sa.Column('benefits_csv', sa.String(2048), nullable=True, server_default=''))
    op.add_column('product_catalog', sa.Column('usage', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('product_catalog', 'usage')
    op.drop_column('product_catalog', 'benefits_csv')
