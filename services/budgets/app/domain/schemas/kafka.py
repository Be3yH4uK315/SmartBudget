from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


class TransactionNewMessage(BaseModel):
    """Kafka-событие создания транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int | None = Field(None, description="ID категории")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionUpdatedMessage(BaseModel):
    """Kafka-событие обновления транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int | None = Field(None, description="Новый ID категории")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class TransactionDeletedMessage(BaseModel):
    """Kafka-событие удаления транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Бизнес-время транзакции")


class BudgetEventMessage(BaseModel):
    """Kafka-событие budget service."""

    model_config = ConfigDict(populate_by_name=True)

    event_type: str = Field(..., description="Тип события бюджета")
    user_id: UUID = Field(..., description="ID пользователя")
    details: dict[str, Any] = Field(default_factory=dict, description="Детали события")


class NotificationEvent(BaseModel):
    """Kafka-событие для notification service."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID = Field(..., description="ID события")
    event_type: str = Field(..., description="Тип notification-события")
    user_id: UUID = Field(..., description="ID пользователя")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Полезная нагрузка уведомления",
    )
    timestamp: datetime = Field(..., description="Время события")
