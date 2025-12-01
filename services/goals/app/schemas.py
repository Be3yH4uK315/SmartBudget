from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import date
from uuid import UUID

class CreateGoalRequest(BaseModel):
    name: str = Field(..., max_length=255, description="Название цели")
    target_value: Decimal = Field(..., gt=0, description="Целевая сумма")
    finish_date: date = Field(..., description="Дата достижения (YYYY-MM-DD)")

class CreateGoalResponse(BaseModel):
    goal_id: UUID

class GoalResponse(BaseModel):
    name: str
    target_value: Decimal
    current_value: Decimal
    finish_date: date
    days_left: int
    status: str

class MainGoalInfo(BaseModel):
    name: str
    target_value: Decimal
    current_value: Decimal

class MainGoalsResponse(BaseModel):
    goals: list[MainGoalInfo]

class AllGoalsResponse(BaseModel):
    goal_id: UUID
    name: str
    target_value: Decimal
    current_value: Decimal
    finish_date: date
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class GoalPatchRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    target_value: Optional[Decimal] = Field(None, gt=0)
    finish_date: Optional[date] = None
    status: Optional[str] = None

class GoalPatchResponse(BaseModel):
    goal_id: UUID
    name: str
    target_value: Decimal
    current_value: Decimal
    finish_date: date
    status: str

class UnifiedErrorResponse(BaseModel):
    detail: str

BUDGET_EVENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Budget Events Schema",
    "type": "object",
    "properties": {
        "event": {"type": "string", "enum": ["goal.created", "goal.updated", "goal.changed"]},
        "goal_id": {"type": "string", "format": "uuid"},
        "user_id": {"type": "string", "format": "uuid"},
        "name": {"type": "string", "maxLength": 255},
        "target_value": {"type": "number", "minimum": 0},
        "current_value": {"type": "number", "minimum": 0},
        "finish_date": {"type": "string", "format": "date"},
        "status": {"type": "string", "enum": ["in_progress", "achieved", "expired", "closed"]},
        "changes": {"type": "object", "additionalProperties": True}
    },
    "required": ["event", "goal_id"],
    "additionalProperties": False
}

BUDGET_NOTIFICATIONS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Budget Notifications Schema",
    "type": "object",
    "properties": {
        "event": {"type": "string", "enum": ["goal.alert", "goal.approaching", "goal.expired"]},
        "goal_id": {"type": "string", "format": "uuid"},
        "type": {"type": "string", "enum": ["achieved", "approaching", "expired"]},
        "days_left": {"type": "integer", "minimum": 0}
    },
    "required": ["event", "goal_id", "type"],
    "additionalProperties": False
}