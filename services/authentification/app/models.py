from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    role = Column(Integer, default=0, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_agent = Column(String, nullable=False)
    device_name = Column(String, nullable=False)
    ip = Column(String, nullable=False)
    location = Column(String, nullable=False)
    revoked = Column(Boolean, default=False)
    refresh_fingerprint = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)