import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_current_user_id, get_notification_repo, get_settings_repo
from app.api.websockets import ws_manager
from app.infrastructure.db.repositories import NotificationRepository, SettingsRepository
from app.domain.schemas.api import (
    PaginatedNotifications, 
    NotificationResponse, 
    NotificationSettingsResponse, 
    NotificationSettingsUpdate
)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

# --- УВЕДОМЛЕНИЯ (NOTIFICATIONS) ---

@router.get("", response_model=PaginatedNotifications)
async def get_notifications(
    user_id: uuid.UUID = Depends(get_current_user_id),
    is_read: Optional[bool] = Query(None, description="Фильтр по статусу прочтения"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    notif_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Получить историю уведомлений с пагинацией."""
    notifications, total = await notif_repo.get_paginated_by_user(user_id, is_read, limit, offset)
    unread_count = await notif_repo.get_unread_count(user_id)
    
    items = []
    for n in notifications:
        items.append(NotificationResponse(
            id=str(n.id),
            createdAt=n.created_at.isoformat(),
            titleKey=n.title_key,
            messageKey=n.message_key,
            type=n.type,
            isRead=n.is_read,
            service=n.service,
            props=n.props
        ))
        
    return PaginatedNotifications(
        total=total,
        unreadCount=unread_count,
        items=items
    )


@router.get("/unread-count")
async def get_unread_count(
    user_id: uuid.UUID = Depends(get_current_user_id),
    notif_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Получить только количество непрочитанных (для бейджа на иконке)."""
    count = await notif_repo.get_unread_count(user_id)
    return {"unreadCount": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    notif_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Отметить конкретное уведомление прочитанным."""
    success = await notif_repo.mark_as_read(notification_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    return {"success": True, "id": str(notification_id)}


@router.post("/read-all")
async def mark_all_as_read(
    user_id: uuid.UUID = Depends(get_current_user_id),
    notif_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Отметить ВСЕ уведомления пользователя прочитанными."""
    updated_count = await notif_repo.mark_all_as_read(user_id)
    return {"success": True, "updatedCount": updated_count}


# --- НАСТРОЙКИ (SETTINGS) ---

@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_settings(
    user_id: uuid.UUID = Depends(get_current_user_id),
    settings_repo: SettingsRepository = Depends(get_settings_repo)
):
    """Получить настройки уведомлений пользователя."""
    settings = await settings_repo.get_or_create(user_id)
    return NotificationSettingsResponse(
        locale=settings.locale,
        emailEnabled=settings.email_enabled,
        pushEnabled=settings.push_enabled,
        disabledServices=settings.disabled_services
    )


@router.patch("/settings", response_model=NotificationSettingsResponse)
async def update_settings(
    payload: NotificationSettingsUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    settings_repo: SettingsRepository = Depends(get_settings_repo)
):
    """Обновить настройки уведомлений пользователя."""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    
    db_update_data = {}
    if "emailEnabled" in update_data: db_update_data["email_enabled"] = update_data["emailEnabled"]
    if "pushEnabled" in update_data: db_update_data["push_enabled"] = update_data["pushEnabled"]
    if "disabledServices" in update_data: db_update_data["disabled_services"] = update_data["disabledServices"]
    if "locale" in update_data: db_update_data["locale"] = update_data["locale"]

    settings = await settings_repo.update(user_id, db_update_data)
    
    return NotificationSettingsResponse(
        locale=settings.locale,
        emailEnabled=settings.email_enabled,
        pushEnabled=settings.push_enabled,
        disabledServices=settings.disabled_services
    )


# --- WEBSOCKETS ---

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket для real-time уведомлений.
    """
    user_id = token 
    
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
