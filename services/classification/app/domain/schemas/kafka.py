from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TransactionNeedCategoryEvent(BaseModel):
    transaction_id: UUID
    user_id: UUID
    account_id: Optional[UUID] = None
    merchant: str
    mcc: Optional[int] = None
    description: Optional[str] = None
    amount: Decimal

class ClassificationClassifiedEvent(BaseModel):
    transaction_id: UUID
    user_id: UUID
    category_id: int
    category_name_snapshot: str
    confidence: float
    source: str

class ClassificationUpdatedEvent(BaseModel):
    transaction_id: UUID
    user_id: UUID
    merchant: Optional[str] = None
    mcc: Optional[int] = None
    description: Optional[str] = None
    old_category_id: Optional[int] = None
    old_category_name: Optional[str] = None
    new_category_id: int
    new_category_name: str

class DLQMessage(BaseModel):
    original_topic: str
    original_message: str
    error: str
    timestamp: datetime
