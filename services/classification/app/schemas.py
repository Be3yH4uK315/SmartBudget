from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class CategorizationResultResponse(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    category_id: int = Field(..., description="ID присвоенной категории")
    category_name: str = Field(..., description="Имя присвоенной категории")
    confidence: float = Field(..., description="Уверенность модели (0.0 до 1.0)")
    source: str = Field(..., description="Источник (rules, ml, manual)")
    model_version: Optional[str] = Field(None, description="Версия модели, если source=ml")

    model_config = ConfigDict(from_attributes=True)

class FeedbackRequest(BaseModel):
    transaction_id: UUID = Field(..., description="ID транзакции")
    correct_category_id: int = Field(..., description="ID категории, которую указал юзер")
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

SCHEMA_NEED_CATEGORY = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "account_id": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"}
    },
    "required": ["transaction_id", "merchant"]
}

SCHEMA_CLASSIFIED = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "category_id": {"type": ["integer", "string"]}, 
        "category_name": {"type": "string"}
    },
    "required": ["transaction_id", "category_id"]
}

SCHEMA_UPDATED = {
    "$schema": "http://json-schema.org/draft-07/schema#", 
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"},
        "old_category": {"type": "string"},
        "new_category_id": {"type": ["integer", "string"]},
        "new_category_name": {"type": "string"}
    },
    "required": ["transaction_id", "new_category_id"]
}

SCHEMA_NEED_CATEGORY_DLQ = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "original_topic": {"type": "string"},
        "original_message": {"type": "string"},
        "error": {"type": "string"},
        "timestamp": {"type": "string"}
    },
    "required": ["original_topic", "original_message", "error", "timestamp"]
}

SCHEMAS_MAP = {
    "transaction.need_category": SCHEMA_NEED_CATEGORY,
    "transaction.classified": SCHEMA_CLASSIFIED,
    "budget.classification.events": SCHEMA_CLASSIFIED,
    "transaction.updated": SCHEMA_UPDATED,
    "classification.dlq": SCHEMA_NEED_CATEGORY_DLQ 
}