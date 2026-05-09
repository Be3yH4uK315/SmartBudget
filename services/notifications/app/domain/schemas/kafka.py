from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncomingNotificationEvent(BaseModel):
    """Схема для всех бизнес-событий платформы."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID = Field(..., description="Уникальный ID события")
    event_type: str = Field(..., description="Строковой код бизнес-события")
    user_id: UUID = Field(..., description="ID пользователя")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Полезная нагрузка")
    timestamp: datetime = Field(default_factory=_utc_now, description="Время возникновения")


class AuthUserEventPayload(BaseModel):
    """Полезная нагрузка события от Auth-сервиса."""
    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(..., description="Email пользователя")
    language: Optional[str] = Field(None, description="Язык пользователя")


class AuthUserEvent(BaseModel):
    """Событие создания/обновления профиля из сервиса Auth."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID
    event_type: str
    user_id: UUID
    payload: AuthUserEventPayload
    timestamp: datetime


class AuthOutboxEvent(BaseModel):
    """Фактический формат событий auth-сервиса из outbox."""
    model_config = ConfigDict(populate_by_name=True)

    event_type: str = Field(..., description="Тип auth-события")
    user_id: Optional[UUID] = Field(None, description="ID пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    new_email: Optional[str] = Field(None, description="Новый email пользователя")
    language: Optional[str] = Field(None, description="Язык пользователя")
    ip: Optional[str] = Field(None, description="IP адрес")
    location: Optional[str] = Field(None, description="Геолокация")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Дополнительная нагрузка")
