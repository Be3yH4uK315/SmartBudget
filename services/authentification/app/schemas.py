from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class VerifyEmailRequest(BaseModel):
    """Запрос для инициирования проверки электронной почты."""
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Email, на который будет отправлена верификационная ссылка"
    )

class VerifyLinkRequest(BaseModel):
    """Модель запроса для проверки токена ссылки."""
    token: str = Field(
        ...,
        title="Token",
        description="Токен, полученный пользователем из email"
    )

class CompleteRegistrationRequest(BaseModel):
    """Модель запроса для завершения регистрации."""
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Электронная почта пользователя"
    )
    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Имя пользователя"
    )
    country: str = Field(
        ...,
        title="Country",
        description="Страна проживания пользователя"
    )
    token: str = Field(
        ...,
        title="Verification Token",
        description="Верификационный токен из email"
    )
    password: str = Field(
        ...,
        min_length=8,
        title="Password",
        description="Пароль пользователя (не менее 8 символов)"
    )

class LoginRequest(BaseModel):
    """Модель запроса для входа в систему."""
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Email пользователя"
    )
    password: str = Field(
        ...,
        title="Password",
        description="Пароль пользователя"
    )

class ResetPasswordRequest(BaseModel):
    """Модель запроса для инициирования сброса пароля."""
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Email, на который отправить ссылку восстановления"
    )

class CompleteResetRequest(BaseModel):
    """Модель запроса для завершения сброса пароля."""
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Email пользователя для сброса пароля"
    )
    token: str = Field(
        ...,
        title="Reset Token",
        description="Токен подтверждения восстановления пароля"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        title="New Password",
        description="Новый пароль (не менее 8 символов)"
    )

class ChangePasswordRequest(BaseModel):
    """Модель запроса на смену пароля."""
    password: str = Field(
        ...,
        title="Current Password",
        description="Текущий пароль пользователя"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        title="New Password",
        description="Новый пароль (не менее 8 символов)"
    )

class TokenValidateRequest(BaseModel):
    """Модель запроса для проверки токена."""
    token: str = Field(
        ...,
        title="JWT Token",
        description="JWT токен, который необходимо проверить"
    )

class UnifiedResponse(BaseModel):
    """Единая модель ответа для всех endpoints."""
    status: str = Field(
        ...,
        title="Status",
        description="Статус результата: 'success' или 'error'"
    )
    action: str = Field(
        ...,
        title="Action",
        description="Название выполненного действия"
    )
    detail: Optional[str] = Field(
        None,
        title="Detail",
        description="Дополнительная информация или сообщение"
    )

class UserInfo(BaseModel):
    """Безопасная информация о пользователе."""
    id: UUID = Field(
        ...,
        title="User ID",
        description="Уникальный идентификатор пользователя"
    )
    email: EmailStr = Field(
        ...,
        title="Email",
        description="Электронная почта пользователя"
    )
    name: str = Field(
        ...,
        title="Name",
        description="Имя пользователя"
    )
    country: str = Field(
        ...,
        title="Country",
        description="Страна пользователя"
    )
    role: str = Field(
        ...,
        title="Role",
        description="Роль пользователя в системе"
    )
    last_login: Optional[datetime] = Field(
        None,
        title="Last Login",
        description="Дата последнего входа пользователя"
    )
    created_at: datetime = Field(
        ...,
        title="Created At",
        description="Дата создания учетной записи"
    )

    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    """Безопасная информация о сессии, передаваемая на фронтенд."""
    id: UUID = Field(
        ...,
        title="Session ID",
        description="Уникальный идентификатор сессии"
    )
    device_name: str = Field(
        ...,
        title="Device Name",
        description="Название или тип устройства"
    )
    location: str = Field(
        ...,
        title="Location",
        description="Примерное географическое местоположение"
    )
    ip: str = Field(
        ...,
        title="IP Address",
        description="IP-адрес сессии"
    )
    created_at: datetime = Field(
        ...,
        title="Created At",
        description="Дата создания сессии"
    )
    is_current_session: bool = Field(
        False,
        title="Is Current Session",
        description="Является ли сессия текущей"
    )

    class Config:
        from_attributes = True

class AllSessionsResponse(BaseModel):
    """Модель ответа для списка всех сессий пользователя."""
    sessions: list[SessionInfo] = Field(
        ...,
        title="Sessions",
        description="Список активных и прошедших сессий пользователя"
    )