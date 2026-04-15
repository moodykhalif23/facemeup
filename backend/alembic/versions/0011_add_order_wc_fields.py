"""Add wc_order_id and total to orders

Revision ID: 0011_add_order_wc_fields
Revises: 0010_add_product_benefits_usage
Create Date: 2026-04-15
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = '0011_add_order_wc_fields'
down_revision: Union[str, None] = '0010_add_product_benefits_usage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('total', sa.Float(), nullable=True))
    op.add_column('orders', sa.Column('wc_order_id', sa.Integer(), nullable=True))
    op.create_index('ix_orders_wc_order_id', 'orders', ['wc_order_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_orders_wc_order_id', table_name='orders')
    op.drop_column('orders', 'wc_order_id')
    op.drop_column('orders', 'total')
