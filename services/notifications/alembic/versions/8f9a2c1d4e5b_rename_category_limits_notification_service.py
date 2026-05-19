"""rename category limits notification service

Revision ID: 8f9a2c1d4e5b
Revises: 3cbbc1bf1931
Create Date: 2026-05-19 17:04:34.283462+00:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = "8f9a2c1d4e5b"
down_revision: Union[str, Sequence[str], None] = "3cbbc1bf1931"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE notifications SET service = 'Limit' WHERE service = 'limitAmount'",
    )
    op.execute(
        """
        UPDATE user_notification_settings
        SET disabled_services = array_replace(disabled_services, 'limitAmount', 'Limit')
        WHERE 'limitAmount' = ANY(disabled_services)
        """,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE notifications SET service = 'limitAmount' WHERE service = 'Limit'",
    )
    op.execute(
        """
        UPDATE user_notification_settings
        SET disabled_services = array_replace(disabled_services, 'Limit', 'limitAmount')
        WHERE 'Limit' = ANY(disabled_services)
        """,
    )
