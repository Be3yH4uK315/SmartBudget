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
    PASSWORD_RESET_STARTED = "user.password_reset_started"
    PASSWORD_RESET_VALIDATED = "user.password_reset_validated"
    PASSWORD_RESET_COMPLETED = "user.password_reset"
    PASSWORD_CHANGED = "user.password_changed"
    VERIFICATION_STARTED = "user.verification_started"
    VERIFICATION_VALIDATED = "user.verification_validated"
    TOKEN_REFRESHED = "user.token_refreshed"
    SESSION_REVOKED = "user.session_revoked"
    PROFILE_UPDATED = "user.profile_updated"
    EMAIL_CHANGE_STARTED = "user.email_change_started"
    EMAIL_CHANGED = "user.email_changed"


class AuthUserPayload(BaseEventPayload):
    """Payload пользовательского события auth service."""

    user_id: UUID | None = Field(None, description="ID пользователя")
    email: EmailStr | None = Field(None, description="Email пользователя")
    old_email: EmailStr | None = Field(None, description="Старый email пользователя")
    new_email: EmailStr | None = Field(None, description="Новый email пользователя")
    name: str | None = Field(None, description="Имя пользователя")
    language: str | None = Field(None, description="Язык пользователя")
    ip: str | None = Field(None, description="IP адрес")
    location: str | None = Field(None, description="Геолокация")
    payload: dict[str, object] = Field(
        default_factory=dict,
        description="Дополнительная нагрузка auth-события",
    )


class UserRegisteredPayload(AuthUserPayload):
    """Payload события регистрации пользователя."""

    user_id: UUID = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    name: str = Field(..., description="Имя пользователя")
    language: str = Field(..., description="Язык пользователя")


class ProfileUpdatedPayload(AuthUserPayload):
    """Payload события обновления профиля пользователя."""

    user_id: UUID = Field(..., description="ID пользователя")
    email: EmailStr | None = Field(None, description="Email пользователя")
    language: str | None = Field(None, description="Язык пользователя")


class EmailChangedPayload(AuthUserPayload):
    """Payload события смены email."""

    user_id: UUID = Field(..., description="ID пользователя")
    old_email: EmailStr | None = Field(None, description="Старый email пользователя")
    new_email: EmailStr = Field(..., description="Новый email пользователя")


def create_auth_event(
    *,
    event_type: AuthEventType | str,
    payload: AuthUserPayload,
) -> EventEnvelope[AuthUserPayload]:
    """Создает событие auth service."""

    resolved_event_type = str(enum_value(event_type))

    return EventEnvelope.create(
        event_type=resolved_event_type,
        source_service=EventSource.AUTH,
        payload=payload,
        idempotency_key=(
            f"{resolved_event_type}:{payload.user_id}"
            if payload.user_id
            else None
        ),
    )


def create_user_registered_event(
    payload: UserRegisteredPayload,
) -> EventEnvelope[UserRegisteredPayload]:
    """Создает событие регистрации пользователя."""

    return EventEnvelope.create(
        event_type=AuthEventType.USER_REGISTERED,
        source_service=EventSource.AUTH,
        payload=payload,
        idempotency_key=f"user.registered:{payload.user_id}",
    )