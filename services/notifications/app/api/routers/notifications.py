from uuid import UUID

from fastapi import APIRouter, Depends, Path

from app.api import dependencies
from app.api.dependencies import NotificationFilters
from app.domain.schemas import api as schemas
from app.services.service import NotificationService

router = APIRouter(tags=["Notifications"])


@router.get(
    "",
    response_model=schemas.PaginatedNotificationsResponse,
    response_model_exclude_none=True,
    summary="Получить список уведомлений",
)
async def get_notifications(
    filters: NotificationFilters = Depends(),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Возвращает список уведомлений пользователя с пагинацией."""
    return await service.get_paginated_notifications(
        user_id=user_id,
        limit=filters.limit,
        offset=filters.offset,
        services=filters.services,
        notification_types=filters.types,
        statuses=filters.statuses,
    )


@router.get(
    "/unread-count",
    response_model=schemas.UnreadCountResponse,
    summary="Получить количество непрочитанных для бейджа",
)
async def get_unread_count(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Возвращает количество непрочитанных уведомлений пользователя."""
    return await service.get_unread_count(user_id)


@router.patch(
    "/read-all",
    response_model=schemas.MarkAllNotificationsReadResponse,
    summary="Отметить все уведомления пользователя прочитанными",
)
async def mark_all_as_read_by_contract(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Отмечает все уведомления пользователя прочитанными."""
    return await service.mark_all_as_read(user_id)


@router.patch(
    "/{notification_id}",
    response_model=schemas.MarkNotificationReadResponse,
    summary="Отметить одно уведомление прочитанным",
)
async def mark_as_read_by_contract(
    notification_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Отмечает одно уведомление пользователя прочитанным."""
    return await service.mark_as_read(user_id, notification_id)
