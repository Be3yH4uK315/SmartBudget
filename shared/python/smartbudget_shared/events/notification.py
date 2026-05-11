from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import (
    BaseEventPayload,
    EventEnvelope,
    EventSource,
    enum_value,
)


class NotificationEventType(StrEnum):
    """Типы событий notification service."""

    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_READ_ALL = "notification.read_all"


class NotificationPayload(BaseEventPayload):
    """Payload notification-события."""

    notification_id: UUID | None = Field(None, description="ID уведомления")
    user_id: UUID = Field(..., description="ID пользователя")
    channel: str | None = Field(None, description="Канал доставки")
    title: str | None = Field(None, description="Заголовок уведомления")
    message: str | None = Field(None, description="Текст уведомления")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительная нагрузка уведомления",
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
        aggregate_id=payload.notification_id,
        user_id=payload.user_id,
        idempotency_key=(
            f"{resolved_event_type}:{payload.notification_id}"
            if payload.notification_id
            else f"{resolved_event_type}:{payload.user_id}"
        ),
    )
