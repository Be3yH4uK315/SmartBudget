"""initial budgets schema

Revision ID: 20260508_budget_contracts
Revises:
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260508_budget_contracts"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("total_income_amount", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("total_limit_amount", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("is_auto_renew", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("budget_id"),
        sa.UniqueConstraint("user_id", "month", name="uq_budgets_user_id_month"),
    )
    op.create_index(op.f("ix_budgets_user_id"), "budgets", ["user_id"], unique=False)
    op.create_index("ix_budgets_user_id_month", "budgets", ["user_id", "month"], unique=False)

    op.create_table(
        "category_limits",
        sa.Column("category_limit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("limit_amount", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("spent_amount", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.budget_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("category_limit_id"),
        sa.UniqueConstraint(
            "budget_id",
            "category_id",
            name="uq_category_limits_budget_id_category_id",
        ),
    )
    op.create_index(op.f("ix_category_limits_budget_id"), "category_limits", ["budget_id"], unique=False)
    op.create_index("ix_category_limits_category_id", "category_limits", ["category_id"], unique=False)

    op.create_table(
        "processed_budget_transactions",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(
        "ix_processed_budget_transactions_user_id",
        "processed_budget_transactions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_processed_budget_transactions_category_id",
        "processed_budget_transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_processed_budget_transactions_month",
        "processed_budget_transactions",
        ["month"],
        unique=False,
    )
    op.create_index(
        "ix_processed_budget_transactions_user_month",
        "processed_budget_transactions",
        ["user_id", "month"],
        unique=False,
    )
    op.create_index(
        "ix_processed_budget_transactions_occurred_at",
        "processed_budget_transactions",
        ["occurred_at"],
        unique=False,
    )

    op.create_table(
        "outbox_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_outbox_created_at_status",
        "outbox_events",
        ["created_at", "status"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_processing",
        "outbox_events",
        ["status", "next_retry_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_processing", table_name="outbox_events")
    op.drop_index("ix_outbox_created_at_status", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_processed_budget_transactions_occurred_at", table_name="processed_budget_transactions")
    op.drop_index("ix_processed_budget_transactions_user_month", table_name="processed_budget_transactions")
    op.drop_index("ix_processed_budget_transactions_month", table_name="processed_budget_transactions")
    op.drop_index("ix_processed_budget_transactions_category_id", table_name="processed_budget_transactions")
    op.drop_index("ix_processed_budget_transactions_user_id", table_name="processed_budget_transactions")
    op.drop_table("processed_budget_transactions")
    op.drop_index("ix_category_limits_category_id", table_name="category_limits")
    op.drop_index(op.f("ix_category_limits_budget_id"), table_name="category_limits")
    op.drop_table("category_limits")
    op.drop_index("ix_budgets_user_id_month", table_name="budgets")
    op.drop_index(op.f("ix_budgets_user_id"), table_name="budgets")
    op.drop_table("budgets")
