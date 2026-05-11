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


class BudgetEventType(StrEnum):
    """Типы событий budget service."""

    BUDGET_CREATED = "budget.created"
    BUDGET_UPDATED = "budget.updated"
    BUDGET_DELETED = "budget.deleted"
    BUDGET_PROGRESS_CHANGED = "budget.progress_changed"
    BUDGET_THRESHOLD_REACHED = "budget.threshold_reached"


class BudgetPayload(BaseEventPayload):
    """Payload события бюджета."""

    budget_id: UUID = Field(..., description="ID бюджета")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int | None = Field(None, description="ID категории")
    limit_amount: Decimal | None = Field(None, description="Лимит бюджета")
    spent_amount: Decimal | None = Field(None, description="Потраченная сумма")
    threshold_percent: int | None = Field(None, description="Порог уведомления в процентах")


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
        aggregate_id=payload.budget_id,
        user_id=payload.user_id,
        idempotency_key=f"{resolved_event_type}:{payload.budget_id}",
    )
