from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import (
    BaseEventPayload,
    EventEnvelope,
    EventSource,
    enum_value,
)


class GoalEventType(StrEnum):
    """Типы событий goal service."""

    GOAL_CREATED = "goal.created"
    GOAL_CHANGED = "goal.changed"
    GOAL_UPDATED = "goal.updated"
    GOAL_DELETED = "goal.deleted"
    GOAL_ACHIEVED = "goal.achieved"
    GOAL_EXPIRED = "goal.expired"
    GOAL_APPROACHING = "goal.approaching"
    GOAL_ALERT = "goal.alert"
    GOAL_COMPLETED = "goal.completed"
    GOAL_PROGRESS_CHANGED = "goal.progress_changed"
    GOAL_TRANSACTION_CREATED = "goal.transaction.created"
    GOAL_TRANSACTION_DELETED = "goal.transaction.deleted"


class GoalPayload(BaseEventPayload):
    """Базовый payload события цели."""

    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID | None = Field(None, description="ID пользователя")
    details: dict[str, object] = Field(
        default_factory=dict,
        description="Детали события цели",
    )


class GoalTransactionPayload(BaseEventPayload):
    """Payload транзакции, связанной с целью."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class GoalTransactionDeletedPayload(BaseEventPayload):
    """Payload удаления транзакции цели."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


def create_goal_event(
    *,
    event_type: GoalEventType | str,
    payload: GoalPayload,
) -> EventEnvelope[GoalPayload]:
    """Создает событие goal service."""

    resolved_event_type = str(enum_value(event_type))

    return EventEnvelope.create(
        event_type=resolved_event_type,
        source_service=EventSource.GOALS,
        payload=payload,
        idempotency_key=f"{resolved_event_type}:{payload.goal_id}",
    )