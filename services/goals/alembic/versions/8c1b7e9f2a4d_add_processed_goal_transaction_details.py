"""add processed goal transaction details

Revision ID: 8c1b7e9f2a4d
Revises: d7a58aac86c3
Create Date: 2026-04-29 16:43:21.628561+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1b7e9f2a4d"
down_revision: Union[str, Sequence[str], None] = "d7a58aac86c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processed_goal_transactions",
        sa.Column(
            "amount",
            sa.DECIMAL(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "processed_goal_transactions",
        sa.Column(
            "transaction_type",
            sa.String(length=50),
            nullable=False,
            server_default="income",
        ),
    )
    op.alter_column(
        "processed_goal_transactions",
        "amount",
        server_default=None,
    )
    op.alter_column(
        "processed_goal_transactions",
        "transaction_type",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("processed_goal_transactions", "transaction_type")
    op.drop_column("processed_goal_transactions", "amount")
