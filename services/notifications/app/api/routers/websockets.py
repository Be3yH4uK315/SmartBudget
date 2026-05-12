from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.websockets import ws_manager
from app.core.config import settings

router = APIRouter(tags=["Notification WebSockets"])

DEV_ENVIRONMENTS = {"dev", "local", "test"}


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

    if not _is_dev_environment():
        return None

    if not token:
        return None

    try:
        return str(UUID(token))
    except ValueError:
        return None


def _is_dev_environment() -> bool:
    """Проверяет, можно ли использовать dev-token для WebSocket."""
    env = getattr(settings.APP, "ENV", None)
    if not env:
        return False

    return str(env).lower() in DEV_ENVIRONMENTS
