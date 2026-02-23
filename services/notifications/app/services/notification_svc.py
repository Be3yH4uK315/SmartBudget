import logging
from arq import ArqRedis

from app.core.registry import EVENT_REGISTRY
from app.domain.schemas.kafka import IncomingNotificationEvent
from app.infrastructure.db.repositories import NotificationRepository, SettingsRepository
# Менеджер вебсокетов(пока не используем): from app.api.websockets import ws_manager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(
        self, 
        notif_repo: NotificationRepository, 
        settings_repo: SettingsRepository, 
        arq_pool: ArqRedis
    ):
        self.notif_repo = notif_repo
        self.settings_repo = settings_repo
        self.arq_pool = arq_pool

    async def process_incoming_event(self, event: IncomingNotificationEvent):
        """
        Главная бизнес-логика обработки события из Kafka.
        """
        route_config = EVENT_REGISTRY.get(event.event_name)
        if not route_config:
            logger.warning(f"Event {event.event_name} not found in registry. Ignored.")
            return

        settings = await self.settings_repo.get_or_create(event.user_id)

        if route_config.service in settings.disabled_services and route_config.service != "Security":
            logger.info(f"User {event.user_id} disabled notifications for {route_config.service}")
            return

        channels = set(route_config.default_channels)
        if not settings.push_enabled:
            channels.discard("PUSH")
        if not settings.email_enabled:
            channels.discard("EMAIL")

        notif_data = {
            "event_id": event.event_id,
            "user_id": event.user_id,
            "service": route_config.service,
            "type": route_config.type,
            "title_key": route_config.title_key,
            "message_key": route_config.message_key,
            "props": event.payload,
        }
        
        notification = await self.notif_repo.create(notif_data)
        
        if not notification:
            logger.info(f"Duplicate event {event.event_id} ignored.")
            return

        # ws_payload = NotificationResponse.model_validate(notification).model_dump(by_alias=True)
        # await ws_manager.send_personal_message(str(event.user_id), ws_payload)

        if "EMAIL" in channels and settings.email:
            await self.arq_pool.enqueue_job(
                "send_email_task",
                email=settings.email,
                locale=settings.locale,
                title_key=route_config.title_key,
                message_key=route_config.message_key,
                props=event.payload
            )

        if "PUSH" in channels and settings.fcm_tokens:
            await self.arq_pool.enqueue_job(
                "send_push_task",
                fcm_tokens=settings.fcm_tokens,
                locale=settings.locale,
                title_key=route_config.title_key,
                message_key=route_config.message_key,
                props=event.payload
            )

        logger.info(f"Processed {event.event_name} for user {event.user_id}. Channels: {channels}")
