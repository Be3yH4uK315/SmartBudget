from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import text

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.services.service import NotificationService
from app.api.websockets import ws_manager

router = APIRouter(tags=["Notifications"])

# --- ПРОБЫ ЗДОРОВЬЯ (HEALTH CHECKS) ---

@router.get("/health/live", status_code=status.HTTP_200_OK, summary="Liveness probe")
async def liveness_check() -> dict:
    return {"status": "ok"}

@router.get("/health/ready", status_code=status.HTTP_200_OK, summary="Readiness probe")
async def readiness_check(request: Request) -> Response:
    app = request.app
    health_status = {"db": "unknown", "arq": "unknown"}
    has_error = False

    engine = getattr(app.state, "engine", None)
    if not engine:
        health_status["db"] = "disconnected"
        has_error = True
    else:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["db"] = "ok"
        except Exception:
            health_status["db"] = "failed"
            has_error = True

    arq_pool = getattr(app.state, "arq_pool", None)
    if not arq_pool:
        health_status["arq"] = "disconnected"
        has_error = True
    else:
        try:
            health_status["arq"] = "ok"
        except Exception:
            health_status["arq"] = "failed"
            has_error = True

    if has_error:
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "components": health_status},
        )
    return ORJSONResponse(content={"status": "ready", "components": health_status})


# --- УВЕДОМЛЕНИЯ (NOTIFICATIONS) ---

@router.get("/", response_model=schemas.PaginatedNotifications, summary="Получить список уведомлений (с пагинацией)")
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="Фильтр по статусу прочтения"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.get_paginated_notifications(user_id, is_read, limit, offset)


@router.get("/unread-count", summary="Получить количество непрочитанных (для бейджа)")
async def get_unread_count(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.get_unread_count(user_id)


@router.patch("/{notification_id}/read", summary="Отметить одно уведомление прочитанным")
async def mark_as_read(
    notification_id: UUID = Path(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.mark_as_read(user_id, notification_id)


@router.post("/read-all", summary="Отметить все уведомления пользователя прочитанными")
async def mark_all_as_read(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.mark_all_as_read(user_id)


# --- НАСТРОЙКИ (SETTINGS) ---

@router.get("/settings", response_model=schemas.NotificationSettingsResponse, summary="Получить настройки уведомлений")
async def get_settings(
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.get_settings(user_id)


@router.patch("/settings", response_model=schemas.NotificationSettingsResponse, summary="Обновить настройки уведомлений")
async def update_settings(
    request: schemas.NotificationSettingsUpdate = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: NotificationService = Depends(dependencies.get_notification_service),
):
    return await service.update_settings(user_id, request)


# --- WEBSOCKETS ---

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(..., description="JWT Токен или ID юзера")):
    """
    WebSocket для real-time уведомлений (колокольчика).
    """
    # TODO: Здесь интеграция с verify_token. Пока считаем токен == user_id.
    user_id = token 
    
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
