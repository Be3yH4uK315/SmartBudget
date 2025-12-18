from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import date
from uuid import UUID

from app import models

class CreateGoalRequest(BaseModel):
    name: str = Field(..., max_length=255, description="Название цели")
    targetValue: Decimal = Field(..., gt=0, description="Целевая сумма")
    finishDate: date = Field(..., description="Дата достижения (YYYY-MM-DD)")

class CreateGoalResponse(BaseModel):
    goalId: UUID = Field(..., description="ID созданной цели")

class GoalResponse(BaseModel):
    name: str = Field(..., description="Название цели")
    targetValue: Decimal = Field(..., description="Целевая сумма")
    currentValue: Decimal = Field(..., description="Текущая накопленная сумма")
    finishDate: date = Field(..., description="Дата достижения")
    daysLeft: int = Field(..., description="Дней осталось")
    status: models.GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: float
        }
    )

class MainGoalInfo(BaseModel):
    name: str = Field(..., description="Название цели")
    targetValue: Decimal = Field(..., description="Целевая сумма")
    currentValue: Decimal = Field(..., description="Текущая накопленная сумма")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: float
        }
    )

class MainGoalsResponse(BaseModel):
    goals: list[MainGoalInfo]

class AllGoalsResponse(BaseModel):
    goalId: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    targetValue: Decimal = Field(..., description="Целевая сумма")
    currentValue: Decimal = Field(..., description="Текущая накопленная сумма")
    finishDate: date = Field(..., description="Дата достижения")
    status: models.GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: float
        }
    )

class GoalPatchRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название цели")
    targetValue: Optional[Decimal] = Field(None, gt=0, description="Целевая сумма")
    finishDate: Optional[date] = Field(None, description="Дата достижения")
    status: Optional[models.GoalStatus] = Field(None, description="Статус цели")

class UnifiedErrorResponse(BaseModel):
    detail: str = Field(..., description="Описание ошибки")

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionEvent(BaseModel):
    transactionId: UUID = Field(..., description="ID транзакции")
    accountId: UUID = Field(..., description="В контексте целей это goalId")
    userId: UUID = Field(..., description="ID пользователя")
    value: Decimal = Field(..., description="Сумма транзакции")
    type: TransactionType = Field(..., pattern="Тип транзакции")

BUDGET_EVENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Budget Events Schema",
    "description": "События, связанные с целями пользователя",
    "type": "object",
    "properties": {
        "event": {
            "type": "string",
            "description": "Тип события",
            "enum": ["goal.created", "goal.updated", "goal.changed"]
        },
        "goalId": {
            "type": "string",
            "format": "uuid",
            "description": "ID цели"
        },
        "userId": {
            "type": "string",
            "format": "uuid",
            "description": "ID пользователя"
        },
        "name": {
            "type": "string",
            "maxLength": 255,
            "description": "Название цели"
        },
        "targetValue": {
            "type": "number",
            "minimum": 0,
            "description": "Целевая сумма"
        },
        "currentValue": {
            "type": "number",
            "minimum": 0,
            "description": "Текущая накопленная сумма"
        },
        "finishDate": {
            "type": "string",
            "format": "date",
            "description": "Дата достижения цели (YYYY-MM-DD)"
        },
        "status": {
            "type": "string",
            "description": "Статус цели",
            "enum": ["ongoing", "achieved", "expired", "closed"]
        },
        "changes": {
            "type": "object",
            "description": "Изменённые поля цели",
            "additionalProperties": True
        }
    },
    "required": ["event", "goalId"],
    "additionalProperties": False
}

BUDGET_NOTIFICATIONS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Budget Notifications Schema",
    "description": "Уведомления, связанные с целями пользователя",
    "type": "object",
    "properties": {
        "event": {
            "type": "string",
            "description": "Тип уведомления",
            "enum": ["goal.alert", "goal.approaching", "goal.expired"]
        },
        "goalId": {
            "type": "string",
            "format": "uuid",
            "description": "ID цели"
        },
        "type": {
            "type": "string",
            "description": "Категория уведомления",
            "enum": ["achieved", "approaching", "expired"]
        },
        "daysLeft": {
            "type": "integer",
            "minimum": 0,
            "description": "Количество дней до даты достижения цели"
        }
    },
    "required": ["event", "goalId", "type"],
    "additionalProperties": False
}