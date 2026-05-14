from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    limit_amount: Decimal = Field(default=0, ge=0, description="Новый лимит категории")

    @model_validator(mode="after")
    def require_limit(self):
        """Проверяет, что limit_amount передан."""
        if self.limit_amount is None:
            raise ValueError("limitAmount is required")

        return self


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


class CategorySettingsResponse(CamelModel):
    """Настройки лимита категории."""

    category_id: int = Field(..., description="ID категории")
    limit_amount: Decimal = Field(..., description="Лимит по категории")


class BudgetResponse(CamelModel):
    """Ответ с бюджетом пользователя."""

    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    total_income_amount: Decimal = Field(..., description="Общая сумма доходов")
    spent_amount: Decimal = Field(..., description="Потраченная сумма")
    is_auto_renew: bool = Field(..., description="Автопродление бюджета")
    categories: list[CategoryResponse] = Field(
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
    transaction_type: str = Field(..., description="Тип транзакции")


class DashboardBudgetResponse(CamelModel):
    """Бюджет для главного экрана."""

    categories: list[DashboardCategoryResponse] = Field(
        default_factory=list,
        description="Категории для главного экрана",
    )
    total_limit_amount: Decimal = Field(..., description="Общий лимит бюджета")
    total_income_amount: Decimal = Field(..., description="Общая сумма доходов")


class CreateBudgetResponse(CamelModel):
    """Ответ после создания бюджета."""

    budget_id: str = Field(..., description="ID созданного бюджета")
