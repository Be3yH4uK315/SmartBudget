from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


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


class CategoryLimitRequest(CamelModel):
    """Лимит по категории при создании бюджета."""

    category_id: int = Field(..., gt=0, description="ID категории")
    limit_amount: Decimal = Field(..., ge=0, description="Лимит по категории")


class CreateBudgetRequest(CamelModel):
    """Запрос на создание бюджета."""

    categories: list[CategoryLimitRequest] = Field(
        default_factory=list,
        description="Список лимитов по категориям",
    )
    total_limit_amount: Decimal | None = Field(
        default=None,
        ge=0,
        description="Общий лимит бюджета",
    )
    is_auto_renew: bool = Field(
        default=False,
        description="Автоматически переносить бюджет на следующий месяц",
    )


class PatchCategoryLimitRequest(CamelModel):
    """Запрос на обновление лимита категории."""

    category_id: int = Field(..., gt=0, description="ID категории")
    limit_amount: Decimal = Field(..., ge=0, description="Новый лимит категории")


class PatchBudgetRequest(CamelModel):
    """Запрос на частичное обновление бюджета."""

    total_limit_amount: Decimal | None = Field(
        default=None,
        ge=0,
        description="Новый общий лимит бюджета",
    )
    is_auto_renew: bool | None = Field(
        default=None,
        description="Автоматически переносить бюджет на следующий месяц",
    )
    categories: list[PatchCategoryLimitRequest] | None = Field(
        default=None,
        description="Список изменений лимитов категорий",
    )


class CategoryResponse(CamelModel):
    """Категория бюджета с лимитом и расходом."""

    category_id: int = Field(..., description="ID категории")
    limit_amount: Decimal = Field(..., description="Лимит по категории")
    spent_amount: Decimal = Field(..., description="Потраченная сумма")
    income_amount: Decimal = Field(..., description="Полученная сумма")


class CreateBudgetResponse(CamelModel):
    """Ответ после создания бюджета."""

    budget_id: UUID = Field(..., description="ID созданного бюджета")
    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    total_income_amount: Decimal = Field(..., description="Общая сумма доходов")
    total_spent_amount: Decimal = Field(..., description="Потраченная сумма")
    is_auto_renew: bool = Field(..., description="Автопродление бюджета")
    categories: list[CategoryResponse] = Field(
        default_factory=list,
        description="Категории бюджета",
    )


class BudgetCategoryResponse(CamelModel):
    """Агрегат транзакций бюджета по категории и типу."""

    category_id: int = Field(..., description="ID категории")
    limit_amount: Decimal = Field(..., description="Лимит по категории")
    amount: Decimal = Field(..., description="Сумма транзакций")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")


class PatchBudgetResponse(CamelModel):
    """Ответ после обновления бюджета."""

    budget_id: UUID = Field(..., description="ID бюджета")
    updated: bool = Field(..., description="Признак успешного обновления")


class CategorySettingsResponse(CamelModel):
    """Настройки лимита категории."""

    category_id: int = Field(..., description="ID категории")
    limit_amount: Decimal = Field(..., description="Лимит по категории")
    income_amount: Decimal = Field(..., description="Полученная сумма")


class BudgetResponse(CamelModel):
    """Ответ с бюджетом пользователя."""

    budget_id: UUID | None = Field(None, description="ID бюджета")
    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    total_income_amount: Decimal = Field(..., description="Общая сумма доходов")
    total_spent_amount: Decimal = Field(..., description="Потраченная сумма")
    is_auto_renew: bool = Field(..., description="Автопродление бюджета")
    categories: list[BudgetCategoryResponse] = Field(
        default_factory=list,
        description="Категории бюджета",
    )


class BudgetSettingsResponse(CamelModel):
    """Ответ с настройками бюджета."""

    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    is_auto_renew: bool = Field(..., description="Автопродление бюджета")
    categories: list[CategorySettingsResponse] = Field(
        default_factory=list,
        description="Настройки категорий",
    )


class DashboardCategoryResponse(CamelModel):
    """Категория бюджета для главного экрана."""

    category_id: int = Field(..., description="ID категории")
    amount: Decimal = Field(..., description="Сумма по категории")
    income_amount: Decimal = Field(..., description="Полученная сумма")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")


class DashboardBudgetResponse(CamelModel):
    """Бюджет для главного экрана."""

    categories: list[BudgetCategoryResponse] = Field(
        default_factory=list,
        description="Категории для главного экрана",
    )
    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    total_income_amount: Decimal = Field(..., description="Общая сумма доходов")


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


class BackfillTransactionItemRequest(CamelModel):
    """Транзакция для ручного восстановления бюджетной статистики."""

    transaction_id: UUID = Field(..., description="ID транзакции")
    account_id: UUID | None = Field(None, description="ID счета")
    category_id: int | None = Field(None, description="ID категории")
    amount: Decimal = Field(..., ge=0, description="Сумма транзакции")
    transaction_type: TransactionType = Field(..., description="Тип транзакции")
    date: datetime = Field(..., description="Время операции")


class BackfillBudgetTransactionsRequest(CamelModel):
    """Запрос восстановления бюджетной статистики по транзакциям."""

    transactions: list[BackfillTransactionItemRequest] = Field(
        default_factory=list,
        description="Транзакции для применения к бюджету",
    )


class BackfillBudgetTransactionsResponse(CamelModel):
    """Результат восстановления бюджетной статистики."""

    applied_count: int = Field(..., ge=0, description="Количество примененных транзакций")
    skipped_count: int = Field(..., ge=0, description="Количество пропущенных транзакций")
