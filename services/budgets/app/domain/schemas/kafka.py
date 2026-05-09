from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TransactionType


class TransactionNewMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID
    user_id: UUID
    category_id: int | None = None
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType
    occurred_at: datetime


class TransactionUpdatedMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID
    user_id: UUID
    old_category_id: int | None = None
    new_category_id: int | None = None
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType
    occurred_at: datetime


class TransactionDeletedMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
