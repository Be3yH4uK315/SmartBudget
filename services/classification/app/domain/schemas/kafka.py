from datetime import datetime
from decimal import Decimal
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class TransactionNeedCategoryEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: UUID = Field(validation_alias=AliasChoices("transaction_id", "transactionId"))
    user_id: Optional[UUID] = Field(default=None, validation_alias=AliasChoices("user_id", "userId"))
    account_id: Optional[UUID] = Field(default=None, validation_alias=AliasChoices("account_id", "accountId"))
    merchant: str
    mcc: Optional[int] = None
    description: Optional[str] = None
    value: Optional[Decimal] = None

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
