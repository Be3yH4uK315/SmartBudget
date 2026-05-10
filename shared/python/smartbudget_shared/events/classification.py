from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import BaseEventPayload, EventEnvelope, EventSource


class ClassificationEventType(StrEnum):
    """Типы событий classification service."""

    CLASSIFICATION_REQUESTED = "classification.requested"
    CLASSIFICATION_COMPLETED = "classification.completed"
    CLASSIFICATION_UPDATED = "classification.updated"
    CLASSIFICATION_FAILED = "classification.failed"

    TRANSACTION_CLASSIFIED = "transaction.classified"
    TRANSACTION_CATEGORY_UPDATED = "transaction.category_updated"


class TransactionNeedCategoryPayload(BaseEventPayload):
    """Payload транзакции, которой нужна категория."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")


class ClassificationCompletedPayload(BaseEventPayload):
    """Payload успешной классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int = Field(..., description="ID категории")
    category_name_snapshot: str = Field(
        ...,
        description="Snapshot имени категории на момент классификации",
    )
    confidence: float = Field(..., description="Уверенность классификации")
    source: str = Field(..., description="Источник классификации")


class ClassificationUpdatedPayload(BaseEventPayload):
    """Payload ручного обновления категории после feedback."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    merchant: str | None = Field(None, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    old_category_name: str | None = Field(None, description="Старое название категории")
    new_category_id: int = Field(..., description="Новый ID категории")
    new_category_name: str = Field(..., description="Новое название категории")


class ClassificationFailedPayload(BaseEventPayload):
    """Payload ошибки классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    error: str = Field(..., description="Описание ошибки классификации")


def create_classification_completed_event(
    payload: ClassificationCompletedPayload,
) -> EventEnvelope[ClassificationCompletedPayload]:
    """Создает событие успешной классификации для transactions service."""

    return EventEnvelope.create(
        event_type=ClassificationEventType.TRANSACTION_CLASSIFIED,
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        idempotency_key=f"transaction.classified:{payload.transaction_id}",
    )


def create_classification_updated_event(
    payload: ClassificationUpdatedPayload,
) -> EventEnvelope[ClassificationUpdatedPayload]:
    """Создает событие ручного обновления категории для transactions service."""

    return EventEnvelope.create(
        event_type=ClassificationEventType.TRANSACTION_CATEGORY_UPDATED,
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        idempotency_key=f"transaction.category_updated:{payload.transaction_id}",
    )


def create_classification_failed_event(
    payload: ClassificationFailedPayload,
) -> EventEnvelope[ClassificationFailedPayload]:
    """Создает событие ошибки классификации."""

    return EventEnvelope.create(
        event_type=ClassificationEventType.CLASSIFICATION_FAILED,
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        idempotency_key=f"classification.failed:{payload.transaction_id}",
    )