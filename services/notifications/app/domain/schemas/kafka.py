from datetime import datetime, timezone
from typing import Any, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from smartbudget_shared.events import (
    AuthUserPayload,
    BudgetPayload,
    EventEnvelope,
    GoalPayload,
    TransactionCategoryChangedPayload,
    TransactionUnclassifiedFoundPayload,
)


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


class IncomingNotificationEvent(BaseModel):
    """Нормализованное входящее событие для создания уведомления."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID = Field(..., description="Уникальный ID события")
    event_type: str = Field(..., description="Строковой код бизнес-события")
    user_id: UUID = Field(..., description="ID пользователя")
    payload: dict[str, Any] = Field(default_factory=dict, description="Payload")
    timestamp: datetime = Field(default_factory=_utc_now, description="Время события")


AuthEvent: TypeAlias = EventEnvelope[AuthUserPayload]
BudgetEvent: TypeAlias = EventEnvelope[BudgetPayload]
GoalEvent: TypeAlias = EventEnvelope[GoalPayload]
TransactionUnclassifiedFoundEvent: TypeAlias = EventEnvelope[
    TransactionUnclassifiedFoundPayload
]
TransactionCategoryChangedEvent: TypeAlias = EventEnvelope[
    TransactionCategoryChangedPayload
]


__all__ = [
    "IncomingNotificationEvent",
    "AuthEvent",
    "BudgetEvent",
    "GoalEvent",
    "TransactionUnclassifiedFoundEvent",
    "TransactionCategoryChangedEvent",
]
