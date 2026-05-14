from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionStatus, TransactionType


def to_camel(string: str) -> str:
    """Преобразует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """Базовая Pydantic-модель с camelCase alias."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={Decimal: float},
    )


class CreateManualTransactionRequest(CamelModel):
    """Запрос на создание ручной транзакции."""

    account_id: UUID | None = Field(None, description="ID счета")
    amount: Decimal = Field(..., ge=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    date: datetime | None = Field(None, description="Время операции")
    category_id: int | None = Field(None, description="ID категории")
    description: str | None = Field("", description="Описание транзакции")
    merchant: str | None = Field(None, description="Название merchant")


class PatchTransactionCategoryRequest(CamelModel):
    """Запрос на изменение категории транзакции."""

    category_id: int | None = Field(None, description="ID новой категории")


class TransactionResponse(CamelModel):
    """Краткая модель транзакции для списка."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    amount: Decimal = Field(..., description="Сумма транзакции")
    category_id: int | None = Field(None, description="ID категории")
    description: str | None = Field(None, description="Описание транзакции")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    status: TransactionStatus = Field(..., description="Статус транзакции")
    date: datetime = Field(..., description="Время операции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")


class TransactionDetailResponse(CamelModel):
    """Детальная модель транзакции."""

    user_id: UUID = Field(..., description="ID пользователя")
    transaction_id: UUID = Field(..., description="ID транзакции")
    account_id: UUID | None = Field(None, description="ID счета")
    category_id: int | None = Field(None, description="ID категории")
    date: datetime = Field(..., description="Время операции")
    amount: Decimal = Field(..., description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    status: TransactionStatus = Field(..., description="Статус транзакции")
    merchant: str = Field(..., description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field(None, description="Описание транзакции")
    created_at: datetime = Field(..., description="Время создания")
    imported_at: datetime = Field(..., description="Время импорта")
    updated_at: datetime = Field(..., description="Время обновления")


class ImportTransactionItem(CamelModel):
    """Элемент mock-импорта транзакции."""

    user_id: UUID | None = Field(None, description="ID пользователя")
    transaction_id: UUID = Field(..., description="ID транзакции")
    account_id: UUID | None = Field(None, description="ID счета")
    date: datetime = Field(..., description="Время операции")
    amount: Decimal = Field(..., ge=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    status: TransactionStatus | None = Field(None, description="Статус транзакции")
    merchant: str | None = Field("", description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field("", description="Описание транзакции")
    category_id: int | None = Field(None, description="ID категории")


class TransactionsByMonth(CamelModel):
    """Сумма транзакций цели за месяц."""

    amount: Decimal = Field(..., description="Сумма транзакций")
    period_start: datetime = Field(..., description="Начало периода")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
