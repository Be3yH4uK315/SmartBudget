from enum import IntEnum
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

def to_camel(string: str) -> str:
    """Конвертирует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class CamelModel(BaseModel):
    """Базовая модель с поддержкой camelCase и alias."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class UserRole(IntEnum):
    """Роли пользователей."""
    USER = 0
    ADMIN = 1
    MODERATOR = 2

# --- Request Models ---

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

# --- Response Models ---

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
    created_at: datetime = Field(..., description="Дата регистрации")

class SessionInfo(CamelModel):
    session_id: UUID = Field(..., description="ID сессии")
    device_name: str = Field(..., description="Устройство")
    location: str = Field(..., description="Локация")
    ip: str = Field(..., description="IP адрес")
    is_current_session: bool = Field(False, description="Текущая ли это сессия")
    last_activity: datetime = Field(..., description="Время последней активности")
    created_at: datetime = Field(..., description="Дата создания")

class AllSessionsResponse(CamelModel):
    sessions: list[SessionInfo]
