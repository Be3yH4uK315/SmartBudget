from uuid import UUID

from fastapi import APIRouter, Body, Depends

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import NotificationService

router = APIRouter(tags=["Push Notifications"])


@router.post("/subscribe", summary="Сохранить browser push подписку")
async def subscribe_push(
    request: schemas.PushSubscribeRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Сохраняет browser push подписку пользователя."""
    return await service.subscribe_push(user_id, request.subscription)


@router.post("/unsubscribe", summary="Удалить browser push подписку")
async def unsubscribe_push(
    request: schemas.PushUnsubscribeRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    """Удаляет browser push подписку пользователя."""
    return await service.unsubscribe_push(user_id, request.endpoint)
