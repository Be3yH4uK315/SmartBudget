from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
import enum

from app import base

class UserRole(enum.IntEnum):
    USER = 0
    ADMIN = 1
    MODERATOR = 2

class User(base.Base):
    __tablename__ = "users"

    userId = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    role = Column(Integer, default=UserRole.USER, nullable=False)
    email = Column(String(255), nullable=False)
    passwordHash = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String, nullable=False)
    isActive = Column(Boolean, default=False)
    lastLogin = Column(DateTime(timezone=True), nullable=True)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updatedAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    __table_args__ = (
        UniqueConstraint('email', name='uq_users_email'),
        Index('ix_users_email', 'email'),
    )

class Session(base.Base):
    __tablename__ = "sessions"

    sessionId = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    userId = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.userId", 
        ondelete="CASCADE"), 
        nullable=False
    )
    userAgent = Column(String, nullable=False)
    deviceName = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    location = Column(String, nullable=False)
    revoked = Column(Boolean, default=False)
    refreshFingerprint = Column(String, nullable=False)
    expiresAt = Column(DateTime(timezone=True), nullable=False)
    createdAt = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index('ix_sessions_user_id', 'userId'),
        Index('ix_sessions_expires_at', 'expiresAt'),
        Index('ix_sessions_fingerprint', 'refreshFingerprint'),
    )