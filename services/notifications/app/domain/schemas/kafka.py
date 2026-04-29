from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class IncomingNotificationEvent(CamelModel):
    """Схема для всех бизнес-событий платформы."""
    event_id: UUID = Field(..., description="Уникальный ID события")
    event_name: str = Field(..., description="Строковой код бизнес-события")
    user_id: UUID = Field(..., description="ID пользователя")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Полезная нагрузка")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время возникновения")

class AuthUserEventPayload(CamelModel):
    """Полезная нагрузка события от Auth-сервиса."""
    email: str = Field(..., description="Email пользователя")
    locale: Optional[str] = Field(None, description="Локаль пользователя")
    language: Optional[str] = Field(None, description="Язык пользователя")

class AuthUserEvent(CamelModel):
    """Событие создания/обновления профиля из сервиса Auth."""
    event_id: UUID
    event_name: str
    user_id: UUID
    payload: AuthUserEventPayload
    timestamp: datetime

class AuthOutboxEvent(CamelModel):
    """Фактический формат событий auth-сервиса из outbox."""
    event_type: str = Field(..., description="Тип auth-события")
    user_id: Optional[UUID] = Field(None, description="ID пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    new_email: Optional[str] = Field(None, description="Новый email пользователя")
    language: Optional[str] = Field(None, description="Язык пользователя")
    locale: Optional[str] = Field(None, description="Локаль пользователя")
    ip: Optional[str] = Field(None, description="IP адрес")
    location: Optional[str] = Field(None, description="Геолокация")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Дополнительная нагрузка")
