from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


class TransactionClassifiedMessage(BaseModel):
    """Kafka-событие классификации транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int = Field(..., description="ID категории")
    confidence: float = Field(..., description="Уверенность классификации")
    source: str = Field(..., description="Источник классификации")


class TransactionCategoryUpdatedMessage(BaseModel):
    """Kafka-событие обновления категории транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int = Field(..., description="Новый ID категории")
    old_category_name: str | None = Field(None, description="Старое название категории")
    new_category_name: str | None = Field(None, description="Новое название категории")


class TransactionNewMessage(BaseModel):
    """Kafka-событие новой транзакции для budget service."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int | None = Field(None, description="ID категории")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Время операции")


class TransactionNewGoalMessage(BaseModel):
    """Kafka-событие новой транзакции цели."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Время операции")


class TransactionImportedMessage(BaseModel):
    """Kafka-событие импорта транзакций."""

    model_config = ConfigDict(populate_by_name=True)

    event_type: str = Field(..., description="Тип события")
    user_id: UUID = Field(..., description="ID пользователя")
    details: dict[str, Any] = Field(default_factory=dict, description="Детали события")


class TransactionNeedCategoryMessage(BaseModel):
    """Kafka-событие транзакции без категории."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")


class TransactionUpdatedMessage(BaseModel):
    """Kafka-событие обновления транзакции для budget service."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int | None = Field(None, description="Новый ID категории")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    occurred_at: datetime = Field(..., description="Время операции")


class TransactionDeletedMessage(BaseModel):
    """Kafka-событие удаления транзакции для budget service."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Время операции")


class BudgetEventMessage(BaseModel):
    """Kafka-событие от budget service."""

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
