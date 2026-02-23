"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "product_catalog",
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ingredients_csv", sa.String(length=1024), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("sku"),
    )

    op.create_table(
        "skin_profile_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("skin_type", sa.String(length=64), nullable=False),
        sa.Column("conditions_csv", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skin_profile_history_user_id"), "skin_profile_history", ["user_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("items_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)

    op.create_table(
        "loyalty_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_loyalty_ledger_user_id"), "loyalty_ledger", ["user_id"], unique=False)

    op.bulk_insert(
        sa.table(
            "product_catalog",
            sa.column("sku", sa.String),
            sa.column("name", sa.String),
            sa.column("ingredients_csv", sa.String),
            sa.column("stock", sa.Integer),
        ),
        [
            {
                "sku": "DRR-ACN-001",
                "name": "Dr Rashel Salicylic Clear Serum",
                "ingredients_csv": "Salicylic Acid,Niacinamide,Tea Tree",
                "stock": 24,
            },
            {
                "sku": "EST-HYD-010",
                "name": "Estelin Deep Hydration Cream",
                "ingredients_csv": "Hyaluronic Acid,Ceramides,Glycerin",
                "stock": 18,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_loyalty_ledger_user_id"), table_name="loyalty_ledger")
    op.drop_table("loyalty_ledger")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_skin_profile_history_user_id"), table_name="skin_profile_history")
    op.drop_table("skin_profile_history")
    op.drop_table("product_catalog")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
