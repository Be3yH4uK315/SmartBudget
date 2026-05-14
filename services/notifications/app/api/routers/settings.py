from uuid import UUID

from fastapi import APIRouter, Body, Depends

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import NotificationService

router = APIRouter(tags=["Notification Settings"])


@router.get(
    "",
    response_model=schemas.NotificationSettingsResponse,
    summary="Получить настройки уведомлений",
)
async def get_settings(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Возвращает настройки уведомлений пользователя."""
    return await service.get_settings(user_id)


@router.patch(
    "",
    response_model=schemas.NotificationSettingsResponse,
    summary="Обновить настройки уведомлений",
)
async def update_settings(
    request: schemas.NotificationSettingsUpdate = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Обновляет настройки уведомлений пользователя."""
    return await service.update_settings(user_id, request)


@router.patch(
    "/status",
    response_model=schemas.NotificationSettingsResponse,
    summary="Включить/выключить уведомления",
)
async def update_notifications_status(
    request: schemas.NotificationStatusUpdate = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Включает или выключает все уведомления пользователя."""
    return await service.update_notifications_status(
        user_id,
        request.notifications_status,
    )
