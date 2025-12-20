from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from decimal import Decimal
from datetime import date
from uuid import UUID

class GoalStatus(Enum):
    ONGOING = 'ongoing'
    ACHIEVED = 'achieved'
    EXPIRED = 'expired'
    CLOSED = 'closed'

class GoalEventType(str, Enum):
    CREATED = "goal.created"
    CHANGED = "goal.changed"
    UPDATED = "goal.updated"
    ACHIEVED = "goal.achieved"
    EXPIRED = "goal.expired"
    APPROACHING = "goal.approaching"
    ALERT = "goal.alert"

class CreateGoalRequest(BaseModel):
    name: str = Field(..., max_length=255, description="Название цели")
    target_value: Decimal = Field(..., gt=0, description="Целевая сумма")
    finish_date: date = Field(..., description="Дата достижения (YYYY-MM-DD)")

class CreateGoalResponse(BaseModel):
    goal_id: UUID = Field(..., description="ID созданной цели")

class GoalResponse(BaseModel):
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: date = Field(..., description="Дата достижения")
    days_left: int = Field(..., description="Дней осталось")
    status: GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )

class MainGoalInfo(BaseModel):
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )

class MainGoalsResponse(BaseModel):
    goals: list[MainGoalInfo]

class AllGoalsResponse(BaseModel):
    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: date = Field(..., description="Дата достижения")
    status: GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )

class GoalPatchRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название цели")
    target_value: Optional[Decimal] = Field(None, gt=0, description="Целевая сумма")
    finish_date: Optional[date] = Field(None, description="Дата достижения")
    status: Optional[GoalStatus] = Field(
        None,
        description="Разрешено только значение CLOSED"
    )

    @field_validator("status")
    @classmethod
    def allow_only_closed(cls, v):
        if v is None:
            return v
        if v != GoalStatus.CLOSED:
            raise ValueError("Only CLOSED status is allowed")
        return v

class UnifiedErrorResponse(BaseModel):
    detail: str = Field(..., description="Описание ошибки")

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionEvent(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    goal_id: UUID = Field(..., description="ID цели")
    user_id: UUID = Field(..., description="ID пользователя")
    value: Decimal = Field(..., gt=0, description="Сумма транзакции")
    type: TransactionType = Field(..., description="Тип транзакции")

    model_config = ConfigDict(from_attributes=True)