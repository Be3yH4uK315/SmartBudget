"""initial notifications schema

Revision ID: 3cbbc1bf1931
Revises:
Create Date: 2026-05-08 09:15:06.001257+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3cbbc1bf1931"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_notification_settings",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False),
        sa.Column("push_enabled", sa.Boolean(), nullable=False),
        sa.Column("disabled_services", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("push_subscriptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_notification_settings_email"),
        "user_notification_settings",
        ["email"],
        unique=True,
    )

    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("service", sa.String(length=50), nullable=False),
        sa.Column("notification_type", sa.String(length=20), nullable=False),
        sa.Column("title_key", sa.String(length=100), nullable=False),
        sa.Column("message_key", sa.String(length=100), nullable=False),
        sa.Column("props", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_notification_settings.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("notification_id"),
    )
    op.create_index(op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False)
    op.create_index(op.f("ix_notifications_event_id"), "notifications", ["event_id"], unique=True)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(
        "ix_notifications_user_id_is_read_created_at",
        "notifications",
        ["user_id", "is_read", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id_is_read_created_at", table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_event_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_created_at"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_user_notification_settings_email"), table_name="user_notification_settings")
    op.drop_table("user_notification_settings")
