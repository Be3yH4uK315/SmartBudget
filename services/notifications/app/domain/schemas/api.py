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
    date: datetime = Field(..., description="Время создания")
    title_key: str = Field(..., description="Ключ перевода заголовка")
    message_key: str = Field(..., description="Ключ перевода текста")
    type: NotificationType = Field(..., description="Тип уведомления")
    is_read: bool = Field(..., description="Прочитано ли")
    service: NotificationServiceType = Field(..., description="Сервис-отправитель")
    props: Optional[Dict[str, Any]] = Field(None, description="Переменные для шаблона")

class PaginatedNotifications(CamelModel):
    """Ответ для списка уведомлений с пагинацией."""
    total: int = Field(..., description="Всего уведомлений")
    unread_count: int = Field(..., description="Количество непрочитанных")
    items: List[NotificationResponse] = Field(..., description="Список уведомлений")

class BudgetNotificationSettings(CamelModel):
    total_limit: bool = Field(..., description="Уведомления по общему бюджету")
    categories_limit: bool = Field(..., description="Уведомления по лимитам категорий")

class NotificationSettingsResponse(CamelModel):
    """Модель текущих настроек пользователя для фронта."""
    notifications_status: bool = Field(..., description="Включены ли уведомления в общем")
    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettings = Field(..., description="Настройки бюджетных уведомлений")

class NotificationSettingsUpdate(CamelModel):
    """Полное обновление настроек уведомлений."""
    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettings = Field(..., description="Настройки бюджетных уведомлений")

class WebPushSubscription(CamelModel):
    endpoint: str = Field(..., description="Browser push endpoint")
    expiration_time: Optional[int] = Field(None, description="Subscription expiration time")
    keys: Dict[str, str] = Field(..., description="Browser push encryption keys")

class PushSubscribeRequest(CamelModel):
    user_id: Optional[str] = Field(None, description="Frontend user id; authoritative user id comes from gateway header")
    subscription: WebPushSubscription = Field(..., description="Browser push subscription")

class PushUnsubscribeRequest(CamelModel):
    user_id: Optional[str] = Field(None, description="Frontend user id; authoritative user id comes from gateway header")
    endpoint: str = Field(..., description="Browser push endpoint")
