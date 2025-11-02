from pydantic import BaseModel, Field, EmailStr
from uuid import UUID

class VerifyEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для верификации")

class VerifyLinkRequest(BaseModel):
    token: str = Field(..., description="Токен из email")

class CompleteRegistrationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для завершения")
    name: str = Field(..., max_length=255, description="Имя пользователя")
    country: str = Field(..., description="Страна")
    token: str = Field(..., description="Верификационный токен")
    password: str = Field(..., min_length=8, description="Пароль")
    user_agent: str = Field(..., description="User-Agent")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., description="Пароль")
    user_agent: str = Field(..., description="User-Agent")

class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для восстановления")

class CompleteResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email для сброса")
    token: str = Field(..., description="Токен восстановления")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class ChangePasswordRequest(BaseModel):
    password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")

class TokenValidateRequest(BaseModel):
    token: str = Field(..., description="JWT токен для валидации")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class StatusResponse(BaseModel):
    ok: bool = Field(True, description="Статус операции")