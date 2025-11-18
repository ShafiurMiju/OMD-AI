"""Add subscription tables

Revision ID: b1f2e3d4c5a6
Revises: a5c220713937
Create Date: 2025-11-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1f2e3d4c5a6"
down_revision: Union[str, None] = "a5c220713937"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription_plan table
    op.create_table(
        "subscription_plan",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("plan_name", sa.String(), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("plan_type", sa.String(), nullable=True),
        sa.Column("duration_type", sa.String(), nullable=True),
        sa.Column("plan_duration", sa.BigInteger(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("benefits", sa.JSON(), nullable=True),
        sa.Column("additional_info", sa.Text(), nullable=True),
        sa.Column("group", sa.String(), nullable=True),
        sa.Column("models", sa.JSON(), nullable=True),
        sa.Column("users", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_subscription table
    op.create_table(
        "user_subscription",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("payment_id", sa.String(), nullable=True),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("start_date", sa.BigInteger(), nullable=True),
        sa.Column("end_date", sa.BigInteger(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better performance
    op.create_index(
        "idx_subscription_plan_is_active", "subscription_plan", ["is_active"]
    )
    op.create_index(
        "idx_subscription_plan_plan_type", "subscription_plan", ["plan_type"]
    )
    op.create_index("idx_user_subscription_user_id", "user_subscription", ["user_id"])
    op.create_index("idx_user_subscription_plan_id", "user_subscription", ["plan_id"])
    op.create_index("idx_user_subscription_status", "user_subscription", ["status"])
    op.create_index(
        "idx_user_subscription_end_date", "user_subscription", ["end_date"]
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_user_subscription_end_date", table_name="user_subscription")
    op.drop_index("idx_user_subscription_status", table_name="user_subscription")
    op.drop_index("idx_user_subscription_plan_id", table_name="user_subscription")
    op.drop_index("idx_user_subscription_user_id", table_name="user_subscription")
    op.drop_index("idx_subscription_plan_plan_type", table_name="subscription_plan")
    op.drop_index("idx_subscription_plan_is_active", table_name="subscription_plan")

    # Drop tables
    op.drop_table("user_subscription")
    op.drop_table("subscription_plan")
