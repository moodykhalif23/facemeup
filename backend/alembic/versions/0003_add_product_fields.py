"""add_product_fields

Revision ID: 0003_add_product_fields
Revises: 0002_roles_refresh
Create Date: 2024-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_product_fields'
down_revision: Union[str, None] = '0002_roles_refresh'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to product_catalog table
    op.add_column('product_catalog', sa.Column('price', sa.Float(), nullable=True))
    op.add_column('product_catalog', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('product_catalog', sa.Column('category', sa.String(length=255), nullable=True))
    op.add_column('product_catalog', sa.Column('image_url', sa.String(length=512), nullable=True))
    op.add_column('product_catalog', sa.Column('wc_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('product_catalog', 'wc_id')
    op.drop_column('product_catalog', 'image_url')
    op.drop_column('product_catalog', 'category')
    op.drop_column('product_catalog', 'description')
    op.drop_column('product_catalog', 'price')
