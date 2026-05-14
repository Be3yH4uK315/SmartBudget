"""add category income amount

Revision ID: e295ae8e505e
Revises: 9353ef7b3aec
Create Date: 2026-05-14 07:36:20.888103+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e295ae8e505e"
down_revision: Union[str, None] = "9353ef7b3aec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "category_limits",
        sa.Column(
            "income_amount",
            sa.DECIMAL(18, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("category_limits", "income_amount", server_default=None)
    op.execute(
        """
        WITH transaction_totals AS (
            SELECT
                b.budget_id,
                p.category_id,
                COALESCE(
                    SUM(p.amount) FILTER (WHERE p.transaction_type = 'expense'),
                    0
                ) AS spent_amount,
                COALESCE(
                    SUM(p.amount) FILTER (WHERE p.transaction_type = 'income'),
                    0
                ) AS income_amount
            FROM processed_budget_transactions p
            JOIN budgets b
              ON b.user_id = p.user_id
             AND b.month = p.month
            WHERE p.category_id IS NOT NULL
            GROUP BY b.budget_id, p.category_id
        )
        UPDATE category_limits cl
           SET spent_amount = transaction_totals.spent_amount,
               income_amount = transaction_totals.income_amount
          FROM transaction_totals
         WHERE cl.budget_id = transaction_totals.budget_id
           AND cl.category_id = transaction_totals.category_id
        """
    )
    op.execute(
        """
        UPDATE budgets b
           SET total_income_amount = COALESCE(
               (
                   SELECT SUM(p.amount)
                     FROM processed_budget_transactions p
                    WHERE p.user_id = b.user_id
                      AND p.month = b.month
                      AND p.transaction_type = 'income'
               ),
               0
           )
        """
    )


def downgrade() -> None:
    op.drop_column("category_limits", "income_amount")
