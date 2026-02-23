from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import NotificationType, NotificationServiceType

def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class NotificationResponse(CamelModel):
    """Модель одного уведомления в списке."""
    id: UUID = Field(..., description="ID уведомления")
    created_at: datetime = Field(..., description="Время создания")
    title_key: str = Field(..., description="Ключ перевода заголовка")
    message_key: str = Field(..., description="Ключ перевода текста")
    type: NotificationType = Field(..., description="Тип уведомления")
    is_read: bool = Field(..., description="Прочитано ли")
    service: NotificationServiceType = Field(..., description="Сервис-отправитель")
    props: Optional[Dict[str, Any]] = Field(None, description="Переменные для шаблона")

    model_config = ConfigDict(from_attributes=True)

class PaginatedNotifications(CamelModel):
    """Ответ для списка уведомлений с пагинацией."""
    total: int = Field(..., description="Всего уведомлений")
    unread_count: int = Field(..., description="Количество непрочитанных")
    items: List[NotificationResponse] = Field(..., description="Список уведомлений")

class NotificationSettingsResponse(CamelModel):
    """Модель текущих настроек пользователя."""
    locale: str = Field(..., description="Язык локализации")
    email_enabled: bool = Field(..., description="Включены ли Email-письма")
    push_enabled: bool = Field(..., description="Включены ли PUSH-уведомления")
    disabled_services: List[str] = Field(..., description="Массив отключенных сервисов")

    model_config = ConfigDict(from_attributes=True)

class NotificationSettingsUpdate(CamelModel):
    """Модель для обновления настроек (PATCH)."""
    locale: Optional[str] = Field(None, max_length=10, description="Язык локализации")
    email_enabled: Optional[bool] = Field(None, description="Включены ли Email-письма")
    push_enabled: Optional[bool] = Field(None, description="Включены ли PUSH-уведомления")
    disabled_services: Optional[List[str]] = Field(None, description="Массив отключенных сервисов")