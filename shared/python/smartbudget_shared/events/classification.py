from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import BaseEventPayload, EventEnvelope, EventSource


class ClassificationEventType(StrEnum):
    """Типы событий classification service."""

    TRANSACTION_CLASSIFIED = "transaction.classified"
    TRANSACTION_CATEGORY_UPDATED = "transaction.category_updated"
    CLASSIFICATION_FAILED = "classification.failed"


class TransactionClassifiedPayload(BaseEventPayload):
    """Payload результата автоматической классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int = Field(..., description="ID категории")
    category_name_snapshot: str | None = Field(
        None,
        description="Snapshot имени категории на момент классификации",
    )
    confidence: float = Field(..., ge=0, le=1, description="Уверенность классификации")
    source: str = Field(..., description="Источник классификации")


class TransactionCategoryUpdatedPayload(BaseEventPayload):
    """Payload ручного обновления категории транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    merchant: str | None = Field(None, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal | None = Field(None, description="Сумма транзакции")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    old_category_name: str | None = Field(None, description="Старое название категории")
    new_category_id: int = Field(..., description="Новый ID категории")
    new_category_name: str | None = Field(None, description="Новое название категории")


class ClassificationFailedPayload(BaseEventPayload):
    """Payload ошибки классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    error: str = Field(..., description="Описание ошибки классификации")


def create_transaction_classified_event(
    payload: TransactionClassifiedPayload,
) -> EventEnvelope[TransactionClassifiedPayload]:
    """Создает событие успешной классификации транзакции."""
    return EventEnvelope.create(
        event_type=ClassificationEventType.TRANSACTION_CLASSIFIED,
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.classified:{payload.transaction_id}",
    )


def create_transaction_category_updated_event(
    payload: TransactionCategoryUpdatedPayload,
) -> EventEnvelope[TransactionCategoryUpdatedPayload]:
    """Создает событие ручного обновления категории транзакции."""
    return EventEnvelope.create(
        event_type=ClassificationEventType.TRANSACTION_CATEGORY_UPDATED,
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
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
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"classification.failed:{payload.transaction_id}",
    )
