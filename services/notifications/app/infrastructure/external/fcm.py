import asyncio
import logging
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

def init_firebase() -> None:
    """Инициализация Firebase Admin SDK. Требует GOOGLE_APPLICATION_CREDENTIALS в переменных окружения."""
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully.")
        except ValueError as e:
            logger.warning("Firebase credentials not found. Push notifications will fail. Error: %s", e)

async def send_push_notifications(tokens: list[str], title: str, body: str, data: dict = None) -> None:
    """Асинхронная массовая отправка Push-уведомлений через Firebase."""
    if not tokens:
        return

    str_data = {str(k): str(v) for k, v in (data or {}).items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=str_data,
        tokens=tokens,
    )

    def _sync_send():
        return messaging.send_each_for_multicast(message)

    try:
        response = await asyncio.to_thread(_sync_send)
        logger.info("FCM: Sent %d messages successfully. Failed: %d", response.success_count, response.failure_count)
    except Exception as e:
        logger.error("FCM Send error: %s", e)
        raise
