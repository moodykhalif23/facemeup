"""Add deleted_at for soft-delete on users and skin_profile_history

Revision ID: 0009_add_soft_delete
Revises: 0008_add_capture_images
Create Date: 2026-04-08
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = '0009_add_soft_delete'
down_revision: Union[str, None] = '0008_add_capture_images'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'], unique=False)

    op.add_column('skin_profile_history', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_skin_profile_history_deleted_at', 'skin_profile_history', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_skin_profile_history_deleted_at', table_name='skin_profile_history')
    op.drop_column('skin_profile_history', 'deleted_at')

    op.drop_index('ix_users_deleted_at', table_name='users')
    op.drop_column('users', 'deleted_at')
