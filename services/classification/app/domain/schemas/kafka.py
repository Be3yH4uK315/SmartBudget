from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TransactionNeedCategoryEvent(BaseModel):
    transaction_id: UUID
    account_id: Optional[UUID] = None
    merchant: str
    mcc: Optional[int] = None
    description: Optional[str] = None

class ClassificationClassifiedEvent(BaseModel):
    transaction_id: UUID
    category_id: int
    category_name: str

class ClassificationUpdatedEvent(BaseModel):
    transaction_id: UUID
    merchant: Optional[str] = None
    mcc: Optional[int] = None
    description: Optional[str] = None
    old_category: Optional[str] = None
    new_category_id: int
    new_category_name: str

class DLQMessage(BaseModel):
    originalTopic: str
    originalMessage: str
    error: str
    timestamp: datetime