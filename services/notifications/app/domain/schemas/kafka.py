from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


class IncomingNotificationEvent(BaseModel):
    """Схема входящего бизнес-события платформы."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID = Field(..., description="Уникальный ID события")
    event_type: str = Field(..., description="Строковой код бизнес-события")
    user_id: UUID = Field(..., description="ID пользователя")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Полезная нагрузка",
    )
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="Время возникновения",
    )


class AuthUserEventPayload(BaseModel):
    """Полезная нагрузка события от auth service."""

    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(..., description="Email пользователя")
    language: str | None = Field(None, description="Язык пользователя")


class AuthUserEvent(BaseModel):
    """Событие создания или обновления профиля из auth service."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: UUID
    event_type: str
    user_id: UUID
    payload: AuthUserEventPayload
    timestamp: datetime


class AuthOutboxEvent(BaseModel):
    """Фактический формат auth-событий из outbox."""

    model_config = ConfigDict(populate_by_name=True)

    event_type: str = Field(..., description="Тип auth-события")
    user_id: UUID | None = Field(None, description="ID пользователя")
    email: str | None = Field(None, description="Email пользователя")
    new_email: str | None = Field(None, description="Новый email пользователя")
    language: str | None = Field(None, description="Язык пользователя")
    ip: str | None = Field(None, description="IP адрес")
    location: str | None = Field(None, description="Геолокация")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительная нагрузка",
    )
