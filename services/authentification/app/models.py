from uuid import uuid4
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, 
    Index, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
import enum

from app import base

class UserRole(enum.IntEnum):
    """Роли пользователей в системе."""
    USER = 0
    ADMIN = 1
    MODERATOR = 2

class User(base.Base):
    """Модель пользователя."""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    role = Column(Integer, default=UserRole.USER, nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint('email', name='uq_users_email'),
        Index('ix_users_email', 'email'),
        Index('ix_users_is_active', 'is_active'),
        CheckConstraint("email ~ '^[^@]+@[^@]+$'", name='ck_email_format'),
    )

    @validates('email')
    def validate_email(self, key, value):
        """Валидирует email."""
        if not value or '@' not in value:
            raise ValueError("Invalid email format")
        return value.lower().strip()

    @validates('name')
    def validate_name(self, key, value):
        """Валидирует имя."""
        if not value or len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value.strip()

class Session(base.Base):
    """Модель сессии пользователя."""
    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    user_agent = Column(String, nullable=False)
    device_name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    location = Column(String, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    refresh_fingerprint = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index('ix_sessions_user_id', 'user_id'),
        Index('ix_sessions_expires_at', 'expires_at'),
        Index('ix_sessions_fingerprint', 'refresh_fingerprint'),
        Index('ix_sessions_revoked', 'revoked'),
        CheckConstraint('refresh_fingerprint != \'\'', name='ck_fingerprint_not_empty'),
    )