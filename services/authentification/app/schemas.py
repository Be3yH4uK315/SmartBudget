from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class VerifyEmailRequest(BaseModel):
    """Запросите модель для инициирования проверки электронной почты."""
    email: EmailStr = Field(..., description="Email для верификации")

class VerifyLinkRequest(BaseModel):
    """Модель запроса для проверки токена ссылки."""
    token: str = Field(..., description="Токен из email")

class CompleteRegistrationRequest(BaseModel):
    """Модель запроса для завершения регистрации."""
    email: EmailStr = Field(..., description="Email для завершения")
    name: str = Field(..., max_length=255, description="Имя пользователя")
    country: str = Field(..., description="Страна")
    token: str = Field(..., description="Верификационный токен")
    password: str = Field(..., min_length=8, description="Пароль")

class LoginRequest(BaseModel):
    """Модель запроса для входа в систему."""
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Пароль")

class ResetPasswordRequest(BaseModel):
    """Модель запроса для инициирования сброса пароля."""
    email: EmailStr = Field(..., description="Email для восстановления")

class CompleteResetRequest(BaseModel):
    """Модель запроса для завершения сброса пароля."""
    email: EmailStr = Field(..., description="Email для сброса")
    token: str = Field(..., description="Токен восстановления")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class ChangePasswordRequest(BaseModel):
    """Модель запроса на смену пароля."""
    password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class TokenValidateRequest(BaseModel):
    """Модель запроса для проверки токена."""
    token: str = Field(..., description="JWT токен для валидации")

class TokenResponse(BaseModel):
    """Модель ответа для токенов."""
    access_token: str
    refresh_token: str

class UnifiedResponse(BaseModel):
    """Единая модель реагирования для всех конечных точек."""
    status: str = Field(..., description="Статус: успешно или ошибка")
    action: str = Field(..., description="Выполненное действие")
    detail: Optional[str] = Field(None, description="Дополнительное подробное сообщение")

class UserInfo(BaseModel):
    """
    Безопасная информация о пользователе.
    """
    id: UUID
    email: EmailStr
    name: str
    country: str
    role: str
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    """
    Безопасная информация о сессии, передаваемая на фронтенд.
    """
    id: UUID
    device_name: str
    location: str
    ip: str
    created_at: datetime
    is_current_session: bool = Field(False, description="Является ли эта сессия текущей")

    class Config:
        from_attributes = True

class AllSessionsResponse(BaseModel):
    """
    Модель ответа для списка всех сессий пользователя.
    """
    sessions: list[SessionInfo]