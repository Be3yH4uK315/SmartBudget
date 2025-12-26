from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from uuid import UUID

# --- API Models ---

class CategorizationResultResponse(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    category_id: int = Field(..., description="ID присвоенной категории")
    category_name: str = Field(..., description="Имя присвоенной категории")
    confidence: float = Field(..., description="Уверенность модели (0.0 до 1.0)")
    source: str = Field(..., description="Источник (rules, ml, manual)")
    model_version: Optional[str] = Field(None, description="Версия модели, если source=ml")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, v):
        if v < 0:
            raise ValueError('Category ID must be non-negative')
        return v

class FeedbackRequest(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    correct_category_id: int = Field(..., description="ID категории, которую указал юзер")
    user_id: Optional[UUID] = Field(None, description="ID пользователя (если есть)")
    comment: Optional[str] = Field(None, max_length=1024, description="Комментарий")

    @field_validator('correct_category_id')
    @classmethod
    def validate_category_id(cls, v):
        if v < 0:
            raise ValueError('Category ID must be non-negative')
        return v

class HealthResponse(BaseModel):
    status: str = Field(...)
    details: dict = Field(...)

class UnifiedSuccessResponse(BaseModel):
    ok: bool = Field(True)
    detail: Optional[str] = Field(None)

# --- Kafka Event Models (Pydantic instead of JSON Schema) ---

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