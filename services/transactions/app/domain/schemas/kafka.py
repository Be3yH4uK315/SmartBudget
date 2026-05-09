from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import TransactionType


class TransactionClassifiedMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    category_id: int
    confidence: float
    source: str


class TransactionCategoryUpdatedMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    old_category_id: int | None = None
    new_category_id: int
    old_category_name: str | None = None
    new_category_name: str | None = None


class TransactionNewMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    category_id: int | None
    amount: Decimal
    transaction_type: TransactionType
    occurred_at: datetime


class TransactionNewGoalMessage(BaseModel):
    transaction_id: UUID
    goal_id: UUID
    user_id: UUID
    amount: Decimal
    transaction_type: TransactionType
    occurred_at: datetime


class TransactionImportedMessage(BaseModel):
    event_type: str
    user_id: UUID
    details: dict[str, Any]


class TransactionNeedCategoryMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    account_id: UUID | None = None
    merchant: str
    mcc: int | None = None
    description: str | None = None
    amount: Decimal


class TransactionUpdatedMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    old_category_id: int | None
    new_category_id: int | None
    amount: Decimal
    transaction_type: TransactionType
    occurred_at: datetime


class TransactionDeletedMessage(BaseModel):
    transaction_id: UUID
    user_id: UUID
    occurred_at: datetime


class BudgetEventMessage(BaseModel):
    event_type: str
    user_id: UUID
    details: dict[str, Any]


class NotificationEvent(BaseModel):
    event_id: UUID
    event_type: str
    user_id: UUID
    payload: dict[str, Any]
    timestamp: datetime
