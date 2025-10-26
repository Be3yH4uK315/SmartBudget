from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)  # Уникальный ID пользователя
    role = Column(Integer, default=0, nullable=False)  # Роль как целое число: 0 - user, 1 - admin и т.д.
    email = Column(String(255), nullable=False)  # Email пользователя
    password_hash = Column(String, nullable=False)  # Хэш пароля
    name = Column(String(255), nullable=False)  # Имя пользователя
    country = Column(String, nullable=False)  # Страна
    is_active = Column(Boolean, default=False)  # Активен ли аккаунт
    last_login = Column(DateTime, nullable=True)  # Последний логин
    created_at = Column(DateTime, default=datetime.now(timezone.utc))  # Дата создания
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))  # Дата обновления

    __table_args__ = (
        Index('ix_users_email', 'email', unique=True),  # Индекс для уникального email
    )

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)  # ID сессии
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # FK на пользователя
    user_agent = Column(String, nullable=False)  # User-Agent
    device_name = Column(String, nullable=False)  # Название устройства
    ip = Column(String, nullable=False)  # IP адрес
    location = Column(String, nullable=False)  # Локация
    revoked = Column(Boolean, default=False)  # Отозвана ли сессия
    refresh_fingerprint = Column(String, nullable=False)  # Fingerprint refresh токена
    expires_at = Column(DateTime, nullable=False)  # Дата истечения
    created_at = Column(DateTime, default=datetime.now(timezone.utc))  # Дата создания

    __table_args__ = (
        Index('ix_sessions_user_id', 'user_id'),  # Индекс для поиска по user_id
        Index('ix_sessions_expires_at', 'expires_at'),  # Индекс для cleanup
    )