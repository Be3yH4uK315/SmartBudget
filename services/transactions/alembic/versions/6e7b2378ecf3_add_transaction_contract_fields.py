"""initial transactions schema

Revision ID: 6e7b2378ecf3
Revises:
Create Date: 2026-05-08 14:28:51.374829+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "6e7b2378ecf3"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("merchant", sa.String(length=500), nullable=False),
        sa.Column("mcc", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_transactions_amount_non_negative"),
        sa.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_transaction_type_allowed",
        ),
        sa.CheckConstraint(
            "status IN ('rejected', 'confirmed', 'pending')",
            name="ck_transactions_status_allowed",
        ),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_transactions_account_id"), "transactions", ["account_id"], unique=False)
    op.create_index(op.f("ix_transactions_category_id"), "transactions", ["category_id"], unique=False)
    op.create_index(
        "ix_transactions_user_occurred",
        "transactions",
        ["user_id", "date"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_filters_v2",
        "transactions",
        ["user_id", "category_id", "transaction_type", "date"],
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
    op.create_index("ix_outbox_created_at_status", "outbox_events", ["created_at", "status"], unique=False)
    op.create_index("ix_outbox_processing", "outbox_events", ["status", "next_retry_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_outbox_processing", table_name="outbox_events")
    op.drop_index("ix_outbox_created_at_status", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_transactions_filters_v2", table_name="transactions")
    op.drop_index("ix_transactions_user_occurred", table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_account_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
