from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import GoalPriority, GoalStatus


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


class CreateGoalRequest(CamelModel):
    """Запрос на создание цели."""

    name: str = Field(..., max_length=255, description="Название цели")
    target_amount: Decimal = Field(..., gt=0, description="Целевая сумма")
    finish_date: date | None = Field(
        None,
        description="Дата достижения YYYY-MM-DD, null для бессрочных целей",
    )
    tags: list[str] = Field(default_factory=list, description="Список тегов")
    priority: GoalPriority | None = Field(None, description="Приоритет")


class CreateGoalResponse(CamelModel):
    """Ответ после создания цели."""

    goal_id: UUID = Field(..., description="ID созданной цели")


class GoalResponse(CamelModel):
    """Детальная информация о цели."""

    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_amount: Decimal = Field(..., description="Целевая сумма")
    current_amount: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: date | None = Field(
        None,
        description="Дата достижения YYYY-MM-DD, null для бессрочных целей",
    )
    days_left: int | None = Field(None, description="Дней осталось")
    status: GoalStatus = Field(..., description="Статус цели")
    tags: list[str] = Field(default_factory=list, description="Список тегов")
    priority: GoalPriority | None = Field(None, description="Приоритет")
    is_archived: bool = Field(..., description="В архиве ли цель")
    recommended_payment: Decimal | None = Field(
        None,
        description="Рекомендованный платеж в этом месяце",
    )


class MainGoalInfo(CamelModel):
    """Краткая информация о цели для главного экрана."""

    name: str = Field(..., description="Название цели")
    target_amount: Decimal = Field(..., description="Целевая сумма")
    current_amount: Decimal = Field(..., description="Текущая накопленная сумма")


class MainGoalsResponse(CamelModel):
    """Ответ со списком целей для главного экрана."""

    goals: list[MainGoalInfo]


class AllGoalsResponse(CamelModel):
    """Краткая информация о цели для списка целей."""

    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_amount: Decimal = Field(..., description="Целевая сумма")
    current_amount: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: date | None = Field(
        None,
        description="Дата достижения YYYY-MM-DD, null для бессрочных целей",
    )
    status: GoalStatus = Field(..., description="Статус цели")
    priority: GoalPriority | None = Field(None, description="Приоритет")
    tags: list[str] = Field(default_factory=list, description="Список тегов")
    is_archived: bool = Field(..., description="В архиве ли цель")


class GoalPatchRequest(CamelModel):
    """Запрос на частичное обновление цели."""

    name: str | None = Field(None, max_length=255, description="Название цели")
    target_amount: Decimal | None = Field(None, gt=0, description="Целевая сумма")
    finish_date: date | None = Field(
        None,
        description="Дата достижения YYYY-MM-DD, null для бессрочных целей",
    )
    tags: list[str] | None = Field(None, description="Список тегов")
    priority: GoalPriority | None = Field(None, description="Приоритет")
    is_archived: bool | None = Field(
        None,
        description="Поместить в архив или восстановить из архива",
    )


class GoalStatusResponse(CamelModel):
    """Ответ с новым статусом цели."""

    status: GoalStatus = Field(..., description="Статус цели")


class GoalArchiveResponse(CamelModel):
    """Ответ с архивным статусом цели."""

    is_archived: bool = Field(..., description="В архиве ли цель")


class GoalSearchResponse(CamelModel):
    """Информация о цели в результатах поиска."""

    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_amount: Decimal = Field(..., description="Целевая сумма")
    current_amount: Decimal = Field(..., description="Текущая накопленная сумма")
    status: GoalStatus = Field(..., description="Статус цели")
    is_archived: bool = Field(..., description="В архиве ли цель")
