from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import GoalStatus

def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={Decimal: float},
    )

class CreateGoalRequest(CamelModel):
    name: str = Field(..., max_length=255, description="Название цели")
    target_value: Decimal = Field(..., gt=0, description="Целевая сумма")
    finish_date: Optional[date] = Field(
        None,
        description="Дата достижения 'YYYY-MM-DD' (null для бессрочных)",
    )
    tags: list[str] = Field(default_factory=list, description="Список тегов")

class CreateGoalResponse(CamelModel):
    goal_id: UUID = Field(..., description="ID созданной цели")

class GoalResponse(CamelModel):
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: Optional[date] = Field(
        None,
        description="Дата достижения 'YYYY-MM-DD' (null для бессрочных)",
    )
    days_left: Optional[int] = Field(None, description="Дней осталось")
    status: GoalStatus = Field(..., description="Статус цели")
    tags: list[str] = Field(default_factory=list, description="Список тегов")
    recommended_payment: Optional[Decimal] = Field(
        None,
        description="Рекомендованный платеж в этом месяце",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )

class MainGoalInfo(CamelModel):
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )

class MainGoalsResponse(CamelModel):
    goals: list[MainGoalInfo]

class AllGoalsResponse(CamelModel):
    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: Optional[date] = Field(
        None,
        description="Дата достижения 'YYYY-MM-DD' (null для бессрочных)",
    )
    status: GoalStatus = Field(..., description="Статус цели")
    tags: list[str] = Field(default_factory=list, description="Список тегов")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )

class GoalPatchRequest(CamelModel):
    name: Optional[str] = Field(None, max_length=255, description="Название цели")
    target_value: Optional[Decimal] = Field(None, gt=0, description="Целевая сумма")
    finish_date: Optional[date] = Field(
        None,
        description="Дата достижения 'YYYY-MM-DD' (null для бессрочных)",
    )
    status: Optional[GoalStatus] = Field(None, description="Статус цели")
    tags: Optional[list[str]] = Field(None, description="Список тегов")