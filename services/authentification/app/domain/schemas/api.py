from enum import IntEnum
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.core.schemas import CamelModel

class UserRole(IntEnum):
    """Роли пользователей."""
    USER = 0
    ADMIN = 1
    MODERATOR = 2

class VerifyEmailRequest(CamelModel):
    email: EmailStr = Field(..., description="Email для верификации")

class VerifyLinkRequest(CamelModel):
    token: str = Field(..., description="Токен из письма")

class CompleteRegistrationRequest(CamelModel):
    email: EmailStr = Field(..., description="Email пользователя")
    name: str = Field(..., max_length=255, description="Имя пользователя")
    country: str = Field(..., description="Страна")
    token: str = Field(..., description="Токен верификации")
    password: str = Field(..., min_length=8, description="Пароль")

class LoginRequest(CamelModel):
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Пароль")

class ResetPasswordRequest(CamelModel):
    email: EmailStr = Field(..., description="Email для сброса пароля")

class CompleteResetRequest(CamelModel):
    email: EmailStr = Field(..., description="Email")
    token: str = Field(..., description="Токен сброса")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class ChangePasswordRequest(CamelModel):
    password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class TokenValidateRequest(CamelModel):
    token: str = Field(..., description="JWT токен")

class UpdateRetentionRequest(CamelModel):
    days: int = Field(..., description="Новый срок жизни сессий (7, 30, 90, 180)")

class UnifiedResponse(CamelModel):
    status: str = Field(..., description="Статус: success/error")
    action: str = Field(..., description="Выполненное действие")
    detail: Optional[str] = Field(None, description="Детали")

class UserInfo(CamelModel):
    user_id: UUID = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Email")
    name: str = Field(..., description="Имя")
    country: str = Field(..., description="Страна")
    role: UserRole = Field(..., description="Роль")
    last_login: Optional[datetime] = Field(None, description="Дата последнего входа")
    retention_days: int = Field(..., description="Настройка срока жизни сессии")
    created_at: datetime = Field(..., description="Дата регистрации")

class SessionInfo(CamelModel):
    session_id: UUID = Field(..., description="ID сессии")
    device_name: str = Field(..., description="Устройство")
    location: str = Field(..., description="Локация")
    ip: str = Field(..., description="IP адрес")
    is_current: bool = Field(False, description="Текущая ли это сессия")
    last_activity: datetime = Field(..., description="Время последней активности")
    created_at: datetime = Field(..., description="Дата создания")

class AllSessionsResponse(CamelModel):
    sessions: list[SessionInfo]

class RetentionInfo(CamelModel):
    days: int = Field(..., description="Текущий срок жизни сессий (в днях)")
