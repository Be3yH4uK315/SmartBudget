from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionNeedCategoryEvent(BaseModel):
    """Kafka-событие транзакции, которой нужна категория."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")


class ClassificationClassifiedEvent(BaseModel):
    """Kafka-событие успешной классификации транзакции."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    category_id: int = Field(..., description="ID категории")
    category_name_snapshot: str = Field(
        ...,
        description="Snapshot имени категории на момент классификации",
    )
    confidence: float = Field(..., description="Уверенность классификации")
    source: str = Field(..., description="Источник классификации")


class ClassificationUpdatedEvent(BaseModel):
    """Kafka-событие ручного обновления категории после feedback."""

    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(..., description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    merchant: str | None = Field(None, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    old_category_name: str | None = Field(None, description="Старое название категории")
    new_category_id: int = Field(..., description="Новый ID категории")
    new_category_name: str = Field(..., description="Новое название категории")


class DLQMessage(BaseModel):
    """Kafka-сообщение для DLQ."""

    model_config = ConfigDict(populate_by_name=True)

    original_topic: str = Field(..., description="Исходный Kafka topic")
    original_message: str = Field(..., description="Исходное сообщение")
    error: str = Field(..., description="Текст ошибки")
    timestamp: datetime = Field(..., description="Время отправки в DLQ")
