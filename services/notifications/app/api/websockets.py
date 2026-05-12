import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Управляет WebSocket-соединениями для мгновенной доставки уведомлений."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Регистрирует новое WebSocket-соединение пользователя."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        logger.info(
            "WebSocket connected for user %s. Active tabs: %s",
            user_id,
            len(self.active_connections[user_id]),
        )

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Удаляет WebSocket-соединение пользователя."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info("WebSocket disconnected for user %s", user_id)

    async def send_personal_message(self, user_id: str, message: dict) -> None:
        """Отправляет JSON-сообщение во все открытые вкладки пользователя."""
        connections = list(self.active_connections.get(user_id, []))
        dead_connections: list[WebSocket] = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error(
                    "Error sending WebSocket message to user %s: %s",
                    user_id,
                    exc,
                    exc_info=True,
                )
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection, user_id)


ws_manager = ConnectionManager()
