from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import date
from uuid import UUID

from app import models

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
    status: models.GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(from_attributes=True) 

class MainGoalInfo(BaseModel):
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")

    model_config = ConfigDict(from_attributes=True)

class MainGoalsResponse(BaseModel):
    goals: list[MainGoalInfo]

class AllGoalsResponse(BaseModel):
    goal_id: UUID = Field(..., description="ID цели")
    name: str = Field(..., description="Название цели")
    target_value: Decimal = Field(..., description="Целевая сумма")
    current_value: Decimal = Field(..., description="Текущая накопленная сумма")
    finish_date: date = Field(..., description="Дата достижения")
    status: models.GoalStatus = Field(..., description="Статус цели")
    
    model_config = ConfigDict(from_attributes=True)

class GoalPatchRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название цели")
    target_value: Optional[Decimal] = Field(None, gt=0, description="Целевая сумма")
    finish_date: Optional[date] = Field(None, description="Дата достижения")
    status: Optional[models.GoalStatus] = Field(None, description="Статус цели")

class UnifiedErrorResponse(BaseModel):
    detail: str = Field(..., description="Описание ошибки")

class TransactionEvent(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    account_id: UUID = Field(..., description="В контексте целей это goal_id")
    user_id: UUID = Field(..., description="ID пользователя")
    amount: Decimal = Field(..., description="Сумма транзакции")
    direction: str = Field(..., pattern="^(income|expense)$")

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
        "goal_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID цели"
        },
        "user_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID пользователя"
        },
        "name": {
            "type": "string",
            "maxLength": 255,
            "description": "Название цели"
        },
        "target_value": {
            "type": "number",
            "minimum": 0,
            "description": "Целевая сумма"
        },
        "current_value": {
            "type": "number",
            "minimum": 0,
            "description": "Текущая накопленная сумма"
        },
        "finish_date": {
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
    "required": ["event", "goal_id"],
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
        "goal_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID цели"
        },
        "type": {
            "type": "string",
            "description": "Категория уведомления",
            "enum": ["achieved", "approaching", "expired"]
        },
        "days_left": {
            "type": "integer",
            "minimum": 0,
            "description": "Количество дней до даты достижения цели"
        }
    },
    "required": ["event", "goal_id", "type"],
    "additionalProperties": False
}