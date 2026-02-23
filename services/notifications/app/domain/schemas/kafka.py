from datetime import datetime
from typing import Any, Dict
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

class AuthUserEvent(CamelModel):
    """Событие создания/обновления профиля из сервиса Auth."""
    event_id: UUID
    event_name: str
    user_id: UUID
    payload: AuthUserEventPayload
    timestamp: datetime
