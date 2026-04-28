"""replace country with language

Revision ID: b1f6e8c2a9d4
Revises: 9c463471c618
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1f6e8c2a9d4"
down_revision: Union[str, None] = "9c463471c618"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "gender", nullable=True)
    op.add_column("users", sa.Column("language", sa.String(length=2), nullable=True))
    op.execute(
        """
        UPDATE users
        SET language = CASE
            WHEN lower(country) IN ('ru', 'russia', 'russian federation', 'россия', 'рф') THEN 'ru'
            WHEN lower(country) = 'en' THEN 'en'
            ELSE 'en'
        END
        """
    )
    op.alter_column("users", "language", nullable=False)
    op.create_check_constraint(
        "ck_users_language_allowed",
        "users",
        "language IN ('ru', 'en')",
    )
    op.drop_column("users", "country")


def downgrade() -> None:
    op.add_column("users", sa.Column("country", sa.String(length=100), nullable=True))
    op.execute(
        """
        UPDATE users
        SET country = CASE
            WHEN language = 'ru' THEN 'Russia'
            ELSE 'Unknown'
        END
        """
    )
    op.alter_column("users", "country", nullable=False)
    op.drop_constraint("ck_users_language_allowed", "users", type_="check")
    op.drop_column("users", "language")
    op.execute("UPDATE users SET gender = 'male' WHERE gender IS NULL")
    op.alter_column("users", "gender", nullable=False)
