from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import NotificationServiceType, NotificationType


def to_camel(string: str) -> str:
    """Преобразует snake_case в camelCase."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """Базовая Pydantic-модель с camelCase alias."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class NotificationResponse(CamelModel):
    """Модель одного уведомления в списке."""

    notification_id: UUID = Field(..., description="ID уведомления")
    created_at: datetime = Field(..., description="Время создания")
    title_key: str = Field(..., description="Ключ перевода заголовка")
    message_key: str = Field(..., description="Ключ перевода текста")
    notification_type: NotificationType = Field(..., description="Тип уведомления")
    is_read: bool = Field(..., description="Прочитано ли")
    service: NotificationServiceType = Field(..., description="Сервис-отправитель")
    props: dict[str, Any] | None = Field(
        None,
        description="Переменные для шаблона",
    )


class PaginatedNotifications(CamelModel):
    """Ответ для списка уведомлений с пагинацией."""

    total: int = Field(..., description="Всего уведомлений")
    unread_count: int = Field(..., description="Количество непрочитанных")
    items: list[NotificationResponse] = Field(..., description="Список уведомлений")


class BudgetNotificationSettings(CamelModel):
    """Настройки бюджетных уведомлений."""

    total_limit: bool = Field(..., description="Уведомления по общему бюджету")
    categories_limit: bool = Field(..., description="Уведомления по лимитам категорий")


class NotificationSettingsResponse(CamelModel):
    """Текущие настройки уведомлений пользователя."""

    notifications_status: bool = Field(
        ...,
        description="Включены ли уведомления в общем",
    )
    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettings = Field(
        ...,
        description="Настройки бюджетных уведомлений",
    )


class NotificationSettingsUpdate(CamelModel):
    """Запрос на обновление настроек уведомлений."""

    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettings = Field(
        ...,
        description="Настройки бюджетных уведомлений",
    )


class WebPushSubscription(CamelModel):
    """Browser push подписка."""

    endpoint: str = Field(..., description="Browser push endpoint")
    expiration_time: int | None = Field(
        None,
        description="Subscription expiration time",
    )
    keys: dict[str, str] = Field(..., description="Browser push encryption keys")


class PushSubscribeRequest(CamelModel):
    """Запрос на сохранение browser push подписки."""

    subscription: WebPushSubscription = Field(
        ...,
        description="Browser push subscription",
    )


class PushUnsubscribeRequest(CamelModel):
    """Запрос на удаление browser push подписки."""

    endpoint: str = Field(..., description="Browser push endpoint")
