from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import BaseEventPayload, EventEnvelope, EventSource


class TransactionEventType(StrEnum):
    """Типы событий transaction service."""

    TRANSACTION_NEW = "transaction.new"
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    TRANSACTION_DELETED = "transaction.deleted"
    TRANSACTION_IMPORTED = "transaction.imported"
    TRANSACTION_NEED_CATEGORY = "transaction.need_category"
    TRANSACTION_CATEGORY_UPDATED = "transaction.category_updated"
    TRANSACTION_CLASSIFIED = "transaction.classified"
    TRANSACTION_GOAL = "transaction.goal"
    GOAL_TRANSACTION_CREATED = "goal.transaction.created"


class TransactionPayload(BaseEventPayload):
    """Payload созданной или обновленной транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int | None = Field(None, description="ID категории")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionUpdatedPayload(BaseEventPayload):
    """Payload обновленной транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int | None = Field(None, description="Новый ID категории")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionDeletedPayload(BaseEventPayload):
    """Payload удаленной транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionNeedCategoryPayload(BaseEventPayload):
    """Payload транзакции, которой требуется классификация."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")


class TransactionCategoryUpdatedPayload(BaseEventPayload):
    """Payload ручного обновления категории транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int = Field(..., description="Новый ID категории")
    old_category_name: str | None = Field(None, description="Старое название категории")
    new_category_name: str | None = Field(None, description="Новое название категории")


class TransactionClassifiedPayload(BaseEventPayload):
    """Payload результата автоматической классификации транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int = Field(..., description="ID категории")
    category_name_snapshot: str | None = Field(
        default=None,
        description="Snapshot имени категории на момент классификации",
    )
    confidence: float = Field(..., description="Уверенность классификации")
    source: str = Field(..., description="Источник классификации")


class GoalTransactionPayload(BaseEventPayload):
    """Payload транзакции, связанной с целью."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionImportedPayload(BaseEventPayload):
    """Payload события импорта транзакций."""

    user_id: UUID = Field(..., description="ID пользователя")
    details: dict[str, object] = Field(
        default_factory=dict,
        description="Детали импорта",
    )


def create_transaction_created_event(
    payload: TransactionPayload,
) -> EventEnvelope[TransactionPayload]:
    """Создает событие создания транзакции."""

    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_CREATED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        idempotency_key=f"transaction.created:{payload.transaction_id}",
    )


def create_transaction_new_event(
    payload: TransactionPayload,
) -> EventEnvelope[TransactionPayload]:
    """Создает legacy-compatible событие новой транзакции."""

    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_NEW,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        idempotency_key=f"transaction.new:{payload.transaction_id}",
    )


def create_transaction_updated_event(
    payload: TransactionUpdatedPayload,
) -> EventEnvelope[TransactionUpdatedPayload]:
    """Создает событие обновления транзакции."""

    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_UPDATED,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
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
        idempotency_key=f"transaction.need_category:{payload.transaction_id}",
    )


def create_transaction_goal_event(
    payload: GoalTransactionPayload,
) -> EventEnvelope[GoalTransactionPayload]:
    """Создает legacy-compatible событие транзакции цели."""

    return EventEnvelope.create(
        event_type=TransactionEventType.TRANSACTION_GOAL,
        source_service=EventSource.TRANSACTIONS,
        payload=payload,
        idempotency_key=f"transaction.goal:{payload.transaction_id}",
    )

def create_goal_transaction_created_event(
    payload: GoalTransactionPayload,
) -> EventEnvelope[GoalTransactionPayload]:
    """Создает событие транзакции цели."""

    return create_transaction_goal_event(payload)