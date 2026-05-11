from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

PayloadT = TypeVar("PayloadT", bound=BaseModel)


def utc_now() -> datetime:
    """Возвращает текущее UTC-время для событийной модели."""
    return datetime.now(timezone.utc)


def generate_event_id() -> UUID:
    """Генерирует уникальный идентификатор события."""
    return uuid4()


def enum_value(value: Any) -> Any:
    """Возвращает value для enum-подобных объектов или исходное значение."""
    return getattr(value, "value", value)


class EventSource(StrEnum):
    """Имена сервисов-источников событий."""

    AUTH = "authentification"
    TRANSACTIONS = "transactions"
    CLASSIFICATION = "classification"
    BUDGETS = "budgets"
    GOALS = "goals"
    NOTIFICATIONS = "notifications"
    LOGS = "logs"


class KafkaTopic(StrEnum):
    """Kafka topics, используемые сервисами SmartBudget."""

    AUTH_EVENTS = "smartbudget.auth.events"
    TRANSACTION_EVENTS = "smartbudget.transactions.events"
    CLASSIFICATION_EVENTS = "smartbudget.classification.events"
    BUDGET_EVENTS = "smartbudget.budgets.events"
    GOAL_EVENTS = "smartbudget.goals.events"
    NOTIFICATION_EVENTS = "smartbudget.notifications.events"
    DLQ = "smartbudget.events.dlq"


class EventEnvelope(BaseModel, Generic[PayloadT]):
    """
    Единая обертка для Kafka-событий.

    Envelope хранит технические метаданные события, а payload содержит
    бизнес-данные конкретного события.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda value: value.isoformat(),
            Decimal: lambda value: str(value),
            UUID: lambda value: str(value),
        },
    )

    event_id: UUID = Field(
        default_factory=generate_event_id,
        description="Уникальный ID события",
    )
    event_type: str = Field(..., description="Строковый тип события")
    source_service: str = Field(..., description="Сервис-источник события")
    version: int = Field(default=1, ge=1, description="Версия контракта события")
    occurred_at: datetime = Field(
        default_factory=utc_now,
        description="Время возникновения события",
    )
    aggregate_id: UUID | None = Field(
        default=None,
        description="ID основной сущности события",
    )
    user_id: UUID | None = Field(
        default=None,
        description="ID пользователя, к которому относится событие",
    )
    correlation_id: UUID | None = Field(
        default=None,
        description="ID цепочки связанных операций",
    )
    causation_id: UUID | None = Field(
        default=None,
        description="ID события или команды, вызвавшей текущее событие",
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Ключ идемпотентности для повторной обработки",
    )
    payload: PayloadT = Field(..., description="Полезная нагрузка события")

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source_service: str,
        payload: PayloadT,
        event_id: UUID | None = None,
        version: int = 1,
        occurred_at: datetime | None = None,
        aggregate_id: UUID | None = None,
        user_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> "EventEnvelope[PayloadT]":
        """Создает envelope для бизнес-события."""
        return cls(
            event_id=event_id or generate_event_id(),
            event_type=str(enum_value(event_type)),
            source_service=str(enum_value(source_service)),
            version=version,
            occurred_at=occurred_at or utc_now(),
            aggregate_id=aggregate_id,
            user_id=user_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            payload=payload,
        )

    def to_kafka_payload(self) -> bytes:
        """Сериализует событие в bytes для отправки в Kafka."""
        return self.model_dump_json(by_alias=True).encode("utf-8")

    def to_dict(self) -> dict[str, Any]:
        """Возвращает dict-представление события."""
        return self.model_dump(mode="json", by_alias=True)


class BaseEventPayload(BaseModel):
    """Базовый класс для payload-схем событий."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda value: value.isoformat(),
            Decimal: lambda value: str(value),
            UUID: lambda value: str(value),
        },
    )


class EventProcessingStatus(StrEnum):
    """Статусы обработки события в inbox/outbox механизмах."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
