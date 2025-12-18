from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class CategorizationResultResponse(BaseModel):
    transactionId: UUID = Field(..., description="ID транзакции")
    categoryId: int = Field(..., description="ID присвоенной категории")
    categoryName: str = Field(..., description="Имя присвоенной категории")
    confidence: float = Field(..., description="Уверенность модели (0.0 до 1.0)")
    source: str = Field(..., description="Источник (rules, ml, manual)")
    modelVersion: Optional[str] = Field(None, description="Версия модели, если source=ml")

    model_config = ConfigDict(from_attributes=True)

class FeedbackRequest(BaseModel):
    transactionId: UUID = Field(..., description="ID транзакции")
    correctCategoryId: int = Field(..., description="ID категории, которую указал юзер")
    userId: Optional[UUID] = Field(None, description="ID пользователя (если есть)")
    comment: Optional[str] = Field(None, max_length=1024, description="Комментарий")

class HealthResponse(BaseModel):
    status: str = Field(...)
    details: dict = Field(...)

class UnifiedSuccessResponse(BaseModel):
    ok: bool = Field(True)
    detail: Optional[str] = Field(None)

class DLQMessage(BaseModel):
    originalTopic: str
    originalMessage: str
    error: str
    timestamp: datetime

SCHEMA_NEED_CATEGORY = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transactionId": {"type": "string", "format": "uuid"},
        "accountId": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"}
    },
    "required": ["transactionId", "merchant"]
}

SCHEMA_CLASSIFIED = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transactionId": {"type": "string", "format": "uuid"},
        "categoryId": {"type": ["integer", "string"]}, 
        "categoryName": {"type": "string"}
    },
    "required": ["transactionId", "categoryId"]
}

SCHEMA_UPDATED = {
    "$schema": "http://json-schema.org/draft-07/schema#", 
    "type": "object",
    "properties": {
        "transactionId": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"},
        "oldCategory": {"type": "string"},
        "newCategoryId": {"type": ["integer", "string"]},
        "newCategoryName": {"type": "string"}
    },
    "required": ["transactionId", "newCategoryId"]
}

SCHEMA_NEED_CATEGORY_DLQ = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "originalTopic": {"type": "string"},
        "originalMessage": {"type": "string"},
        "error": {"type": "string"},
        "timestamp": {"type": "string"}
    },
    "required": ["originalTopic", "originalMessage", "error", "timestamp"]
}

SCHEMAS_MAP = {
    "transaction.needCategory": SCHEMA_NEED_CATEGORY,
    "transaction.classified": SCHEMA_CLASSIFIED,
    "budget.classification.events": SCHEMA_CLASSIFIED,
    "transaction.updated": SCHEMA_UPDATED,
    "classification.dlq": SCHEMA_NEED_CATEGORY_DLQ 
}