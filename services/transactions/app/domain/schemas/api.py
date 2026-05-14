from datetime import datetime
from decimal import Decimal
from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

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

    transaction_id: UUID = Field(..., description="ID транзакции внешнего банка")

    account_id: UUID | None = Field(None, description="ID счета")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    date: datetime | None = Field(None, description="Время операции")
    category_id: int | None = Field(None, description="ID категории")
    description: str | None = Field("", max_length=2000, description="Описание транзакции")
    merchant: str | None = Field(None, max_length=500, description="Название merchant")


class CreateManualTransactionResponse(CamelModel):
    """Ответ после создания ручной транзакции."""

    transaction_id: UUID = Field(..., description="ID созданной транзакции")


class PatchTransactionCategoryRequest(CamelModel):
    """Запрос на изменение категории транзакции."""

    category_id: int | None = Field(None, description="ID новой категории")


class PatchTransactionCategoryResponse(CamelModel):
    """Ответ после изменения категории транзакции."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    old_category_id: int | None = Field(None, description="Старый ID категории")
    new_category_id: int | None = Field(None, description="Новый ID категории")


class DeleteTransactionResponse(CamelModel):
    """Ответ после удаления транзакции."""

    transaction_id: UUID = Field(..., description="ID удаленной транзакции")
    deleted: bool = Field(..., description="Признак удаления")


class ImportTransactionItemRequest(CamelModel):
    """Элемент запроса mock-импорта транзакции."""

    user_id: UUID | None = Field(None, description="ID пользователя")
    transaction_id: UUID = Field(..., description="ID транзакции")
    account_id: UUID | None = Field(None, description="ID счета")
    date: datetime = Field(..., description="Время операции")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    status: TransactionStatus | None = Field(None, description="Статус транзакции")
    merchant: str | None = Field("", max_length=500, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field("", max_length=2000, description="Описание транзакции")
    category_id: int | None = Field(None, description="ID категории")


ImportMockTransactionsPayload: TypeAlias = (
    ImportTransactionItemRequest | list[ImportTransactionItemRequest]
)


class ImportMockTransactionsRequest(RootModel[ImportMockTransactionsPayload]):
    """Запрос на mock-импорт одной или нескольких транзакций."""


class ImportMockTransactionsResponse(CamelModel):
    """Ответ после mock-импорта транзакций."""

    imported_count: int = Field(..., ge=0, description="Количество импортированных транзакций")


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


class TransactionsByMonthResponse(CamelModel):
    """Сумма транзакций цели за месяц."""

    amount: Decimal = Field(..., description="Сумма транзакций")
    period_start: datetime = Field(..., description="Начало периода")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")


class HealthCheckResponse(CamelModel):
    """Ответ health check."""

    status: str = Field(..., description="Статус сервиса")


class ReadinessResponse(CamelModel):
    """Ответ readiness check."""

    status: str = Field(..., description="Статус готовности сервиса")
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Статусы внешних зависимостей",
    )