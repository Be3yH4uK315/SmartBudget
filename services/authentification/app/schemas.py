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
    user_agent: str = Field(..., description="User-Agent")

class LoginRequest(BaseModel):
    """Модель запроса для входа в систему."""
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Пароль")
    user_agent: str = Field(..., description="User-Agent")

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