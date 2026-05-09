from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

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
    payload: Any = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Включает или выключает уведомления пользователя."""
    notifications_status = _extract_notifications_status(payload)

    return await service.update_notifications_status(user_id, notifications_status)


def _extract_notifications_status(payload: Any) -> bool:
    """Извлекает boolean status из body."""
    if isinstance(payload, bool):
        return payload

    if isinstance(payload, dict) and isinstance(payload.get("status"), bool):
        return payload["status"]

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Payload must be boolean or object with boolean 'status'",
    )
