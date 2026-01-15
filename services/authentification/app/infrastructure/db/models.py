from uuid import uuid4
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates, relationship

from app.infrastructure.db.base import Base
from app.domain.schemas import api as schemas
from app.utils import time

class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    role = Column(Integer, default=schemas.UserRole.USER.value, nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    retention_days = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=time.utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=time.utc_now, onupdate=time.utc_now)

    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_is_active", "is_active"),
        Index("ix_users_is_locked", "is_locked"),
        CheckConstraint(
            "email ~ '^[^@]+@[^@]+$'",
            name="ck_users_email_format",
        ),
        CheckConstraint(
            f"role IN ({', '.join(str(r.value) for r in schemas.UserRole)})",
            name="ck_users_role_allowed",
        ),
    )

    @validates("email")
    def validate_email(self, _, value: str) -> str:
        if not value or "@" not in value:
            raise ValueError("Invalid email format")
        return value.lower().strip()

    @validates("name")
    def validate_name(self, _, value: str) -> str:
        if not value or len(value.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value.strip()

    @validates("country")
    def validate_country(self, _, value: str) -> str:
        if not value:
            raise ValueError("Country is required")
        return value.strip()


class Session(Base):
    """Модель сессии пользователя."""
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_agent = Column(String, nullable=False)
    device_name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    location = Column(String, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    refresh_fingerprint = Column(String(64), nullable=False, unique=True)
    last_activity = Column(DateTime(timezone=True), nullable=False, default=time.utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=time.utc_now)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_expires_at", "expires_at"),
        Index("ix_sessions_revoked", "revoked"),
        CheckConstraint(
            "refresh_fingerprint <> ''",
            name="ck_sessions_fingerprint_not_empty",
        ),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    topic = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=time.utc_now, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    next_retry_at = Column(DateTime(timezone=True), default=time.utc_now, nullable=False)

    __table_args__ = (
        Index('ix_outbox_created_at', 'created_at'),
        Index('ix_outbox_pending_retry', 'status', 'next_retry_at'),
    )