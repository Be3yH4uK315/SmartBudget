from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.websockets import ws_manager

router = APIRouter(tags=["Notification WebSockets"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None, description="User ID для локального dev-доступа"),
):
    """WebSocket endpoint для real-time уведомлений."""
    user_id = _resolve_websocket_user_id(websocket, token)

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)


def _resolve_websocket_user_id(
    websocket: WebSocket,
    token: str | None,
) -> str | None:
    """Извлекает user_id для WebSocket из gateway header или dev-token."""
    user_id = websocket.headers.get("x-user-id")
    if user_id:
        return user_id

    if not token:
        return None

    try:
        return str(UUID(token))
    except ValueError:
        return None
