from datetime import datetime
import enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Literal, Optional

class UserRole(enum.IntEnum):
    """Роли пользователей в системе."""
    USER = 0
    ADMIN = 1
    MODERATOR = 2

class KafkaTopics(str, enum.Enum):
    AUTH_EVENTS = "auth.events"

class AuthEventTypes(str, enum.Enum):
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    PASSWORD_RESET_STARTED = "user.password_reset_started"
    PASSWORD_RESET_VALIDATED = "user.password_reset_validated"
    PASSWORD_RESET_COMPLETED = "user.password_reset"
    PASSWORD_CHANGED = "user.password_changed"
    VERIFICATION_STARTED = "user.verification_started"
    VERIFICATION_VALIDATED = "user.verification_validated"
    TOKEN_REFRESHED = "user.token_refreshed"
    SESSION_REVOKED = "user.session_revoked"

# --- API Request Models ---

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

# --- API Response Models ---

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
    user_id: UUID = Field(
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
    role: UserRole = Field(
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

    model_config = ConfigDict(from_attributes=True)

class SessionInfo(BaseModel):
    """Безопасная информация о сессии, передаваемая на фронтенд."""
    session_id: UUID = Field(
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

    model_config = ConfigDict(from_attributes=True)

class AllSessionsResponse(BaseModel):
    """Модель ответа для списка всех сессий пользователя."""
    sessions: list[SessionInfo] = Field(
        ...,
        title="Sessions",
        description="Список активных и прошедших сессий пользователя"
    )

# --- Kafka Event Models ---

class BaseAuthEvent(BaseModel):
    event: AuthEventTypes
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    )

class UserEvent(BaseAuthEvent):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    ip: Optional[str] = None
    location: Optional[str] = None

class UserRegisteredEvent(UserEvent):
    event: Literal[AuthEventTypes.USER_REGISTERED]
    user_id: UUID
    email: EmailStr
    name: str