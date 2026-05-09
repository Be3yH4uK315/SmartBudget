from datetime import datetime
from enum import Enum, IntEnum
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.core.schemas import CamelModel


class UserRole(IntEnum):
    """Роли пользователей."""

    USER = 0
    ADMIN = 1
    MODERATOR = 2


class Gender(str, Enum):
    """Пол пользователя."""

    MALE = "male"
    FEMALE = "female"


class Language(str, Enum):
    """Поддерживаемые языки интерфейса."""

    RU = "ru"
    EN = "en"


class VerifyEmailRequest(CamelModel):
    """Запрос на начало верификации email."""

    email: EmailStr = Field(..., description="Email для верификации")


class VerifyLinkRequest(CamelModel):
    """Запрос на проверку ссылки верификации."""

    token: str = Field(..., description="Токен из письма")


class CompleteRegistrationRequest(CamelModel):
    """Запрос на завершение регистрации пользователя."""

    email: EmailStr = Field(..., description="Email пользователя")
    name: str = Field(..., max_length=255, description="Имя пользователя")
    gender: Gender | None = Field(None, description="Пол пользователя")
    language: Language = Field(..., description="Язык интерфейса")
    token: str = Field(..., description="Токен верификации")
    password: str = Field(..., min_length=8, description="Пароль")


class LoginRequest(CamelModel):
    """Запрос на вход пользователя."""

    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Пароль")


class ResetPasswordRequest(CamelModel):
    """Запрос на начало сброса пароля."""

    email: EmailStr = Field(..., description="Email для сброса пароля")


class CompleteResetRequest(CamelModel):
    """Запрос на завершение сброса пароля."""

    email: EmailStr = Field(..., description="Email")
    token: str = Field(..., description="Токен сброса")
    new_password: str = Field(..., min_length=8, description="Новый пароль")


class ChangePasswordRequest(CamelModel):
    """Запрос на смену пароля."""

    password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")


class TokenValidateRequest(CamelModel):
    """Запрос на валидацию JWT."""

    token: str = Field(..., description="JWT токен")


class UpdateRetentionRequest(CamelModel):
    """Запрос на изменение срока хранения сессий."""

    days: Literal[7, 30, 90, 180] = Field(
        ...,
        description="Новый срок жизни сессий: 7, 30, 90 или 180 дней",
    )


class UpdateProfileRequest(CamelModel):
    """Запрос на обновление профиля пользователя."""

    name: str = Field(..., min_length=2, max_length=255, description="Новое имя")
    gender: Gender | None = Field(None, description="Пол пользователя")


class UpdateLanguageRequest(CamelModel):
    """Запрос на изменение языка интерфейса."""

    language: Language = Field(..., description="Язык интерфейса")


class InitiateEmailChangeRequest(CamelModel):
    """Запрос на начало смены email."""

    new_email: EmailStr = Field(..., description="Новый email")
    password: str = Field(..., description="Текущий пароль для подтверждения")


class ConfirmEmailChangeRequest(CamelModel):
    """Запрос на подтверждение смены email."""

    token: str = Field(..., description="Токен подтверждения смены email")


class UnifiedResponse(CamelModel):
    """Единый ответ для успешных и ошибочных операций."""

    status: str = Field(..., description="Статус: success/error")
    action: str = Field(..., description="Выполненное действие")
    detail: str | None = Field(None, description="Детали")


class UserInfo(CamelModel):
    """Информация о текущем пользователе."""

    user_id: UUID = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Email")
    name: str = Field(..., description="Имя")
    language: Language = Field(..., description="Язык интерфейса")
    role: UserRole = Field(..., description="Роль")
    last_login: datetime | None = Field(None, description="Дата последнего входа")
    retention_days: int = Field(..., description="Настройка срока жизни сессии")
    created_at: datetime = Field(..., description="Дата регистрации")


class SessionInfo(CamelModel):
    """Информация о пользовательской сессии."""

    session_id: UUID = Field(..., description="ID сессии")
    device_name: str = Field(..., description="Устройство")
    location: str = Field(..., description="Локация")
    ip: str = Field(..., description="IP адрес")
    is_current: bool = Field(False, description="Текущая ли это сессия")
    last_activity: datetime = Field(..., description="Время последней активности")
    created_at: datetime = Field(..., description="Дата создания")


class AllSessionsResponse(CamelModel):
    """Ответ со списком активных сессий пользователя."""

    sessions: list[SessionInfo]


class RetentionInfo(CamelModel):
    """Текущие настройки хранения сессий."""

    days: int = Field(..., description="Текущий срок жизни сессий в днях")
