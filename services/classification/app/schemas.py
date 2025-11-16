from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class CategorizationResultResponse(BaseModel):
    """Модель ответа для GET /classification/{id}"""
    transaction_id: UUID
    category_id: UUID
    category_name: str
    confidence: float
    source: str
    model_version: Optional[str] = None

    class Config:
        from_attributes = True

class FeedbackRequest(BaseModel):
    """Модель запроса для POST /feedback"""
    transaction_id: UUID
    correct_category_id: UUID
    user_id: Optional[UUID] = None
    comment: Optional[str] = Field(None, max_length=1024)

class HealthResponse(BaseModel):
    """Модель ответа для GET /health"""
    status: str
    details: dict

class UnifiedSuccessResponse(BaseModel):
    """Единый ответ для успешных POST/PUT операций"""
    ok: bool = True
    detail: Optional[str] = None