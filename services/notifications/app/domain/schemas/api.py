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


class PaginatedNotificationsResponse(CamelModel):
    """Ответ для списка уведомлений с пагинацией."""

    total: int = Field(..., ge=0, description="Всего уведомлений")
    unread_count: int = Field(..., ge=0, description="Количество непрочитанных")
    items: list[NotificationResponse] = Field(
        default_factory=list,
        description="Список уведомлений",
    )


class UnreadCountResponse(CamelModel):
    """Ответ с количеством непрочитанных уведомлений."""

    unread_count: int = Field(..., ge=0, description="Количество непрочитанных")


class MarkNotificationReadResponse(CamelModel):
    """Ответ после отметки одного уведомления прочитанным."""

    success: bool = Field(..., description="Признак успешной операции")
    notification_id: UUID = Field(..., description="ID уведомления")


class MarkAllNotificationsReadResponse(CamelModel):
    """Ответ после отметки всех уведомлений прочитанными."""

    success: bool = Field(..., description="Признак успешной операции")
    updated_count: int = Field(..., ge=0, description="Количество обновленных уведомлений")


class BudgetNotificationSettingsRequest(CamelModel):
    """Настройки бюджетных уведомлений в request."""

    total_limit: bool = Field(..., description="Уведомления по общему бюджету")
    categories_limit: bool = Field(..., description="Уведомления по лимитам категорий")


class BudgetNotificationSettingsResponse(CamelModel):
    """Настройки бюджетных уведомлений в response."""

    total_limit: bool = Field(..., description="Уведомления по общему бюджету")
    categories_limit: bool = Field(..., description="Уведомления по лимитам категорий")


class NotificationStatusUpdateRequest(CamelModel):
    """Запрос на включение или выключение всех уведомлений."""

    notifications_status: bool = Field(
        ...,
        description="Включены ли уведомления в общем",
    )


class NotificationSettingsResponse(CamelModel):
    """Текущие настройки уведомлений пользователя."""

    notifications_status: bool = Field(
        ...,
        description="Включены ли уведомления в общем",
    )
    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    email_status: bool = Field(..., description="Включены ли EMAIL-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettingsResponse = Field(
        ...,
        description="Настройки бюджетных уведомлений",
    )


class NotificationSettingsUpdateRequest(CamelModel):
    """Запрос на обновление настроек уведомлений."""

    push_status: bool = Field(..., description="Включены ли PUSH-уведомления")
    email_status: bool = Field(..., description="Включены ли EMAIL-уведомления")
    goals: bool = Field(..., description="Уведомления целей")
    transactions: bool = Field(..., description="Уведомления транзакций")
    budget: BudgetNotificationSettingsRequest = Field(
        ...,
        description="Настройки бюджетных уведомлений",
    )


class WebPushSubscriptionRequest(CamelModel):
    """Browser push подписка."""

    endpoint: str = Field(..., min_length=1, description="Browser push endpoint")
    expiration_time: int | None = Field(
        None,
        description="Subscription expiration time",
    )
    keys: dict[str, str] = Field(..., description="Browser push encryption keys")


class PushSubscribeRequest(CamelModel):
    """Запрос на сохранение browser push подписки."""

    subscription: WebPushSubscriptionRequest = Field(
        ...,
        description="Browser push subscription",
    )


class PushSubscriptionResponse(CamelModel):
    """Ответ после изменения browser push подписок."""

    success: bool = Field(..., description="Признак успешной операции")
    subscriptions_count: int = Field(..., ge=0, description="Количество push-подписок")


class PushUnsubscribeRequest(CamelModel):
    """Запрос на удаление browser push подписки."""

    endpoint: str = Field(..., min_length=1, description="Browser push endpoint")


class HealthCheckResponse(CamelModel):
    """Ответ health check."""

    status: str = Field(..., description="Статус сервиса")


class ReadinessResponse(CamelModel):
    """Ответ readiness check."""

    status: str = Field(..., description="Статус готовности сервиса")
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Статусы внешних зависимостей",
    )
