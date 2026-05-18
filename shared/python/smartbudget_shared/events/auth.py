from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import EmailStr, Field

from smartbudget_shared.events.base import (
    BaseEventPayload,
    EventEnvelope,
    EventSource,
    enum_value,
)


class AuthEventType(StrEnum):
    """Типы событий authentification service."""

    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"

    PASSWORD_CHANGED = "user.password_changed"
    PROFILE_UPDATED = "user.profile_updated"
    EMAIL_CHANGED = "user.email_changed"

    DEVICE_NEW_LOGIN = "auth.device.new_login"
    ACTIVITY_SUSPICIOUS = "auth.activity.suspicious"
    SESSION_REVOKED = "auth.session_revoked"


class AuthUserPayload(BaseEventPayload):
    """Payload пользовательского события auth service."""

    user_id: UUID = Field(..., description="ID пользователя")
    session_id: UUID | None = Field(None, description="ID пользовательской сессии")

    email: EmailStr | None = Field(None, description="Email пользователя")
    old_email: EmailStr | None = Field(None, description="Старый email пользователя")
    new_email: EmailStr | None = Field(None, description="Новый email пользователя")

    name: str | None = Field(None, description="Имя пользователя")
    language: str | None = Field(None, description="Язык пользователя")

    ip: str | None = Field(None, description="IP адрес")
    device: str | None = Field(None, description="Устройство пользователя")
    location: str | None = Field(None, description="Геолокация")
    reason: str | None = Field(None, description="Причина события безопасности")

    logged_at: datetime | None = Field(None, description="Время входа")
    changed_at: datetime | None = Field(None, description="Время изменения")
    detected_at: datetime | None = Field(None, description="Время обнаружения")


class UserRegisteredPayload(AuthUserPayload):
    """Payload события регистрации пользователя."""

    email: EmailStr = Field(..., description="Email пользователя")
    name: str = Field(..., description="Имя пользователя")
    language: str = Field(default="ru", description="Язык пользователя")


class ProfileUpdatedPayload(AuthUserPayload):
    """Payload события обновления профиля пользователя."""

    pass


class EmailChangedPayload(AuthUserPayload):
    """Payload события смены email."""

    old_email: EmailStr | None = Field(None, description="Старый email пользователя")
    new_email: EmailStr = Field(..., description="Новый email пользователя")


class PasswordChangedPayload(AuthUserPayload):
    """Payload события смены пароля."""

    changed_at: datetime | None = Field(None, description="Время смены пароля")


class NewLoginPayload(AuthUserPayload):
    """Payload события нового входа."""

    ip: str | None = Field(None, description="IP адрес")
    device: str | None = Field(None, description="Устройство пользователя")
    location: str | None = Field(None, description="Геолокация")
    logged_at: datetime | None = Field(None, description="Время входа")


class SuspiciousActivityPayload(AuthUserPayload):
    """Payload события подозрительной активности."""

    reason: str | None = Field(None, description="Причина подозрительной активности")
    ip: str | None = Field(None, description="IP адрес")
    device: str | None = Field(None, description="Устройство пользователя")
    location: str | None = Field(None, description="Геолокация")
    detected_at: datetime | None = Field(None, description="Время обнаружения")


def create_auth_event(
    *,
    event_type: AuthEventType | str,
    payload: AuthUserPayload,
) -> EventEnvelope[AuthUserPayload]:
    """Создает событие auth service."""
    resolved_event_type = str(enum_value(event_type))
    idempotency_parts = [resolved_event_type, str(payload.user_id)]
    if payload.session_id:
        idempotency_parts.append(str(payload.session_id))

    return EventEnvelope.create(
        event_type=resolved_event_type,
        source_service=EventSource.AUTH,
        payload=payload,
        aggregate_id=payload.user_id,
        user_id=payload.user_id,
        idempotency_key=":".join(idempotency_parts),
    )


def create_user_registered_event(
    payload: UserRegisteredPayload,
) -> EventEnvelope[UserRegisteredPayload]:
    """Создает событие регистрации пользователя."""
    return EventEnvelope.create(
        event_type=AuthEventType.USER_REGISTERED,
        source_service=EventSource.AUTH,
        payload=payload,
        aggregate_id=payload.user_id,
        user_id=payload.user_id,
        idempotency_key=f"user.registered:{payload.user_id}",
    )
