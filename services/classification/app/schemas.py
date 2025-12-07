from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class CategorizationResultResponse(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    category_id: UUID = Field(..., description="ID присвоенной категории")
    category_name: str = Field(..., description="Имя присвоенной категории")
    confidence: float = Field(..., description="Уверенность модели (0.0 до 1.0)")
    source: str = Field(..., description="Источник (rules, ml, manual)")
    model_version: Optional[str] = Field(None, description="Версия модели, если source=ml")

    model_config = ConfigDict(from_attributes=True)

class FeedbackRequest(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    correct_category_id: UUID = Field(..., description="ID категории, которую указал юзер")
    user_id: Optional[UUID] = Field(None, description="ID пользователя (если есть)")
    comment: Optional[str] = Field(None, max_length=1024, description="Комментарий")

class HealthResponse(BaseModel):
    status: str = Field(...)
    details: dict = Field(...)

class UnifiedSuccessResponse(BaseModel):
    ok: bool = Field(True)
    detail: Optional[str] = Field(None)

class DLQMessage(BaseModel):
    original_topic: str
    original_message: str
    error: str
    timestamp: datetime