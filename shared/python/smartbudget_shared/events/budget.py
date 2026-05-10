from enum import StrEnum
from uuid import UUID

from pydantic import Field

from smartbudget_shared.events.base import (
    BaseEventPayload,
    EventEnvelope,
    EventSource,
    enum_value,
)


class BudgetEventType(StrEnum):
    """Типы событий budget service."""

    BUDGET_CREATED = "budget.created"
    BUDGET_UPDATED = "budget.updated"
    BUDGET_DELETED = "budget.deleted"
    BUDGET_SETTINGS_CHANGED = "budget.settings_changed"
    BUDGET_LIMIT_EXCEEDED = "budget.limit_exceeded"
    BUDGET_PROGRESS_CHANGED = "budget.progress_changed"


class BudgetPayload(BaseEventPayload):
    """Базовый payload события бюджета."""

    budget_id: UUID | None = Field(None, description="ID бюджета")
    user_id: UUID = Field(..., description="ID пользователя")
    details: dict[str, object] = Field(
        default_factory=dict,
        description="Детали события бюджета",
    )


def create_budget_event(
    *,
    event_type: BudgetEventType | str,
    payload: BudgetPayload,
) -> EventEnvelope[BudgetPayload]:
    """Создает событие budget service."""

    resolved_event_type = str(enum_value(event_type))

    return EventEnvelope.create(
        event_type=resolved_event_type,
        source_service=EventSource.BUDGETS,
        payload=payload,
        idempotency_key=(
            f"{resolved_event_type}:{payload.budget_id}"
            if payload.budget_id
            else f"{resolved_event_type}:{payload.user_id}"
        ),
    )
