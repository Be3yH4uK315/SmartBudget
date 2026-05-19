from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

from app.domain.enums import TransactionStatus, TransactionType


def to_camel(string: str) -> str:
    """Преобразует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


def _ensure_utc_datetime(value: datetime) -> datetime:
    """Возвращает datetime в UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _serialize_utc_datetime(value: datetime) -> str:
    """Сериализует datetime в UTC ISO-8601 с Z."""
    return _ensure_utc_datetime(value).isoformat().replace("+00:00", "Z")


def _date_only_to_current_utc_time(value):
    """Дополняет date-only input текущим временем UTC."""
    if isinstance(value, datetime):
        return value

    parsed_date: date | None = None
    if isinstance(value, date):
        parsed_date = value
    elif isinstance(value, str):
        raw_value = value.strip()
        if len(raw_value) == 10:
            try:
                parsed_date = date.fromisoformat(raw_value)
            except ValueError:
                return value

    if parsed_date is None:
        return value

    now = _utc_now()
    return datetime.combine(parsed_date, now.timetz())


class CamelModel(BaseModel):
    """Базовая Pydantic-модель с camelCase alias."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={Decimal: float, datetime: _serialize_utc_datetime},
    )


class CreateManualTransactionRequest(CamelModel):
    """Запрос на создание ручной транзакции."""

    account_id: UUID | None = Field(None, description="ID счета")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    status: TransactionStatus = Field(..., description="Статус транзакции")
    date: datetime = Field(..., description="Время операции")
    category_id: int | None = Field(None, description="ID категории")
    description: str | None = Field("", max_length=2000, description="Описание транзакции")
    merchant: str = Field(..., max_length=500, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")

    @field_validator("date", mode="before")
    @classmethod
    def fill_date_only_time(cls, value):
        """Дополняет date-only input текущим временем UTC."""
        return _date_only_to_current_utc_time(value)

    @field_validator("date")
    @classmethod
    def normalize_date_to_utc(cls, value: datetime) -> datetime:
        """Нормализует время операции в UTC."""
        return _ensure_utc_datetime(value)


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

    transaction_id: UUID | None = Field(None, description="ID транзакции")
    user_id: UUID = Field(..., description="ID пользователя")
    account_id: UUID | None = Field(None, description="ID счета")
    date: datetime = Field(..., description="Время операции")
    amount: Decimal = Field(..., gt=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    status: TransactionStatus = Field(..., description="Статус транзакции")
    merchant: str = Field(..., max_length=500, description="Название merchant")
    mcc: int | None = Field(None, description="MCC код")
    description: str | None = Field("", max_length=2000, description="Описание транзакции")
    category_id: int | None = Field(None, description="ID категории")

    @field_validator("date", mode="before")
    @classmethod
    def fill_date_only_time(cls, value):
        """Дополняет date-only input текущим временем UTC."""
        return _date_only_to_current_utc_time(value)

    @field_validator("date")
    @classmethod
    def normalize_date_to_utc(cls, value: datetime) -> datetime:
        """Нормализует время операции в UTC."""
        return _ensure_utc_datetime(value)


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
