from datetime import datetime

from pydantic import Field

from smartbudget_shared.events.base import BaseEventPayload, EventEnvelope, EventSource, utc_now


class DLQPayload(BaseEventPayload):
    """Payload сообщения для dead letter queue."""

    original_topic: str = Field(..., description="Исходный Kafka topic")
    original_message: str = Field(..., description="Исходное сообщение")
    error: str = Field(..., description="Текст ошибки")
    consumer_group: str | None = Field(None, description="Consumer group")
    retry_count: int = Field(default=0, ge=0, description="Количество попыток обработки")
    failed_at: datetime = Field(
        default_factory=utc_now,
        description="Время ошибки обработки",
    )


def create_dlq_event(payload: DLQPayload) -> EventEnvelope[DLQPayload]:
    """Создает DLQ-событие."""

    return EventEnvelope.create(
        event_type="event.dead_letter",
        source_service=EventSource.LOGS,
        payload=payload,
    )