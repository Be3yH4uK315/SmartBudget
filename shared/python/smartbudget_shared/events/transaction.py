from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import BaseEventPayload, EventEnvelope, EventSource


class TransactionEventType(StrEnum):
    """Типы событий transaction service."""

    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    TRANSACTION_DELETED = "transaction.deleted"
    TRANSACTION_NEED_CATEGORY = "transaction.need_category"
    TRANSACTION_GOAL_APPLIED = "transaction.goal_applied"


class TransactionPayload(BaseEventPayload):
    """Payload созданной транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    category_id: int | None = Field(None, description="ID категории")
    category_name_snapshot: str | None = Field(
        None,
        description="Snapshot названия категории",
    )
    goal_id: UUID | None = Field(None, description="ID цели, если транзакция относится к цели")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    merchant: str | None = Field(None, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionUpdatedPayload(TransactionPayload):
    """Payload обновленной транзакции."""

    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int | None = Field(None, description="Новый ID категории")
    old_amount: Decimal | None = Field(None, description="Старая сумма транзакции")
    new_amount: Decimal | None = Field(None, description="Новая сумма транзакции")


class TransactionDeletedPayload(BaseEventPayload):
    """Payload удаленной транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    category_id: int | None = Field(None, description="ID категории")
    goal_id: UUID | None = Field(None, description="ID цели")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionNeedCategoryPayload(BaseEventPayload):
    """Payload транзакции, которой требуется классификация."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    merchant: str | None = Field(None, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionGoalAppliedPayload(BaseEventPayload):
    """Payload транзакции, направленной в цель."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


def create_transaction_created_event(
    payload: TransactionPayload,
) -> EventEnvelope[TransactionPayload]:
    """Создает событие создания транзакции."""
    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_CREATED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.created:{payload.transaction_id}",
    )


def create_transaction_updated_event(
    payload: TransactionUpdatedPayload,
) -> EventEnvelope[TransactionUpdatedPayload]:
    """Создает событие обновления транзакции."""
    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_UPDATED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.updated:{payload.transaction_id}",
    )


def create_transaction_deleted_event(
    payload: TransactionDeletedPayload,
) -> EventEnvelope[TransactionDeletedPayload]:
    """Создает событие удаления транзакции."""
    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_DELETED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.deleted:{payload.transaction_id}",
    )


def create_transaction_need_category_event(
    payload: TransactionNeedCategoryPayload,
) -> EventEnvelope[TransactionNeedCategoryPayload]:
    """Создает событие необходимости классификации транзакции."""
    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_NEED_CATEGORY,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.need_category:{payload.transaction_id}",
    )


def create_transaction_goal_applied_event(
    payload: TransactionGoalAppliedPayload,
) -> EventEnvelope[TransactionGoalAppliedPayload]:
    """Создает событие применения транзакции к цели."""
    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_GOAL_APPLIED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        aggregate_id=payload.transaction_id,
        user_id=payload.user_id,
        idempotency_key=f"transaction.goal_applied:{payload.transaction_id}",
    )
