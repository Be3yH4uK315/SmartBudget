from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import EmailStr, Field

from smartbudget_shared.events.base import (
    BaseEventPayload,
    EventEnvelope,
    EventSource,
    enum_value,
)


class NotificationEventType(StrEnum):
    """Типы событий notification service."""

    NOTIFICATION_REQUESTED = "notification.requested"
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"

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


class NotificationPayload(BaseEventPayload):
    """Payload notification-события."""

    user_id: UUID = Field(..., description="ID пользователя")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Полезная нагрузка уведомления",
    )


class AuthUserEventPayload(BaseEventPayload):
    """Payload пользовательского события от auth service."""

    email: EmailStr = Field(..., description="Email пользователя")
    language: str | None = Field(None, description="Язык пользователя")


class AuthOutboxPayload(BaseEventPayload):
    """
    Payload фактических auth-событий из outbox.

    Нужен для обратной совместимости с текущим auth service,
    где часть данных лежит в корне payload.
    """

    user_id: UUID | None = Field(None, description="ID пользователя")
    email: EmailStr | None = Field(None, description="Email пользователя")
    old_email: EmailStr | None = Field(None, description="Старый email пользователя")
    new_email: EmailStr | None = Field(None, description="Новый email пользователя")
    name: str | None = Field(None, description="Имя пользователя")
    language: str | None = Field(None, description="Язык пользователя")
    ip: str | None = Field(None, description="IP адрес")
    location: str | None = Field(None, description="Геолокация")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительная нагрузка",
    )


def create_notification_event(
    *,
    event_type: NotificationEventType | str,
    payload: NotificationPayload,
) -> EventEnvelope[NotificationPayload]:
    """Создает событие notification service."""

    resolved_event_type = str(enum_value(event_type))

    return EventEnvelope.create(
        event_type=resolved_event_type,
        source_service=EventSource.NOTIFICATIONS,
        payload=payload,
        idempotency_key=f"{resolved_event_type}:{payload.user_id}",
    )