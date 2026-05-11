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
    GOAL_UPDATED = "goal.updated"
    GOAL_DELETED = "goal.deleted"
    GOAL_COMPLETED = "goal.completed"
    GOAL_EXPIRED = "goal.expired"
    GOAL_PROGRESS_CHANGED = "goal.progress_changed"
    GOAL_THRESHOLD_REACHED = "goal.threshold_reached"


class GoalPayload(BaseEventPayload):
    """Payload события цели."""

    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    target_amount: Decimal | None = Field(None, description="Целевая сумма")
    current_amount: Decimal | None = Field(None, description="Текущая накопленная сумма")
    progress_percent: int | None = Field(None, description="Процент выполнения цели")
    threshold_percent: int | None = Field(None, description="Порог уведомления в процентах")


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
        aggregate_id=payload.goal_id,
        user_id=payload.user_id,
        idempotency_key=f"{resolved_event_type}:{payload.goal_id}",
    )
