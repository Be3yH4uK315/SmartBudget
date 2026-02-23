import logging
from uuid import UUID
from arq import ArqRedis

from app.core import exceptions, metrics
from app.core.registry import EVENT_REGISTRY
from app.domain.enums import NotificationServiceType
from app.domain.schemas import api as api_schemas, kafka as k_schemas
from app.infrastructure.db import uow
from app.api.websockets import ws_manager

logger = logging.getLogger(__name__)

class NotificationService:
    """Бизнес-логика маршрутизации и управления уведомлениями."""

    def __init__(self, unit_of_work: uow.UnitOfWork, arq_pool: ArqRedis | None = None):
        self.uow = unit_of_work
        self.arq_pool = arq_pool

    # --- KAFKA EVENT HANDLERS ---

    async def process_auth_event(self, event: k_schemas.AuthUserEvent) -> None:
        """Слушает топик Auth для синхронизации email пользователя."""
        async with self.uow:
            await self.uow.settings.upsert_profile(
                user_id=event.user_id,
                email=event.payload.email
            )
            await self.uow.commit()
            logger.info("Synchronized profile for user %s from Auth event.", event.user_id)

    async def process_incoming_event(self, event: k_schemas.IncomingNotificationEvent) -> None:
        """Основная обработка бизнес-событий из платформы (Budget, Goals, etc.)."""
        route_config = EVENT_REGISTRY.get(event.event_name)
        if not route_config:
            logger.warning("Event '%s' not found in registry. Ignored.", event.event_name)
            return

        async with self.uow:
            settings = await self.uow.settings.get_by_user_id(event.user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(event.user_id, "unknown@example.com")
                await self.uow.commit()

            if (
                route_config.service.value in settings.disabled_services 
                and route_config.service != NotificationServiceType.SECURITY
            ):
                logger.info("User %s disabled notifications for %s. Ignored.", event.user_id, route_config.service.value)
                return

            channels = set(route_config.default_channels)
            if not settings.push_enabled:
                channels.discard("PUSH")
            if not settings.email_enabled:
                channels.discard("EMAIL")

            notif_data = {
                "event_id": event.event_id,
                "user_id": event.user_id,
                "service": route_config.service.value,
                "type": route_config.type.value,
                "title_key": route_config.title_key,
                "message_key": route_config.message_key,
                "props": event.payload,
            }
            
            async with self.uow.make_savepoint():
                notification = await self.uow.notifications.create(notif_data)

            if not notification:
                logger.info("Duplicate event %s ignored.", event.event_id)
                return

            await self.uow.commit()

        metrics.NOTIFICATIONS_CREATED_TOTAL.labels(
            service=route_config.service.value, 
            type=route_config.type.value
        ).inc()

        if self.arq_pool:
            if "EMAIL" in channels and settings.email != "unknown@example.com":
                await self.arq_pool.enqueue_job(
                    "send_email_task",
                    user_id=event.user_id,
                    email=settings.email,
                    locale=settings.locale,
                    title_key=route_config.title_key,
                    message_key=route_config.message_key,
                    props=event.payload
                )
                metrics.BACKGROUND_TASKS_ENQUEUED.labels(task_name="send_email_task").inc()

            if "PUSH" in channels and settings.fcm_tokens:
                await self.arq_pool.enqueue_job(
                    "send_push_task",
                    user_id=event.user_id,
                    fcm_tokens=settings.fcm_tokens,
                    locale=settings.locale,
                    title_key=route_config.title_key,
                    message_key=route_config.message_key,
                    props=event.payload
                )
                metrics.BACKGROUND_TASKS_ENQUEUED.labels(task_name="send_push_task").inc()

        ws_payload = api_schemas.NotificationResponse.model_validate(notification).model_dump(by_alias=True)
        ws_event = {"event_type": "new_notification", "data": ws_payload}
        await ws_manager.send_personal_message(str(event.user_id), ws_event)

    # --- REST API METHODS ---

    async def get_paginated_notifications(
        self, user_id: UUID, is_read: bool | None, limit: int, offset: int
    ) -> api_schemas.PaginatedNotifications:
        """Получает историю уведомлений для UI."""
        async with self.uow:
            notifications, total = await self.uow.notifications.get_paginated(user_id, is_read, limit, offset)
            unread_count = await self.uow.notifications.get_unread_count(user_id)

        items = [api_schemas.NotificationResponse.model_validate(n) for n in notifications]
        return api_schemas.PaginatedNotifications(
            total=total,
            unread_count=unread_count,
            items=items
        )

    async def get_unread_count(self, user_id: UUID) -> dict:
        async with self.uow:
            count = await self.uow.notifications.get_unread_count(user_id)
        return {"unreadCount": count}

    async def mark_as_read(self, user_id: UUID, notification_id: UUID) -> dict:
        async with self.uow:
            success = await self.uow.notifications.mark_as_read(notification_id, user_id)
            if not success:
                raise exceptions.NotificationNotFoundError("Notification not found or already read")
            await self.uow.commit()
        return {"success": True, "id": str(notification_id)}

    async def mark_all_as_read(self, user_id: UUID) -> dict:
        async with self.uow:
            updated_count = await self.uow.notifications.mark_all_as_read(user_id)
            await self.uow.commit()
        return {"success": True, "updatedCount": updated_count}

    async def get_settings(self, user_id: UUID) -> api_schemas.NotificationSettingsResponse:
        async with self.uow:
            settings = await self.uow.settings.get_by_user_id(user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(user_id, "unknown@example.com")
                await self.uow.commit()
        return api_schemas.NotificationSettingsResponse.model_validate(settings)

    async def update_settings(
        self, user_id: UUID, request: api_schemas.NotificationSettingsUpdate
    ) -> api_schemas.NotificationSettingsResponse:
        async with self.uow:
            changes = request.model_dump(exclude_unset=True)
            settings = await self.uow.settings.update_settings(user_id, changes)
            if not settings:
                raise exceptions.NotificationServiceError("Settings profile not found")
            await self.uow.commit()
        return api_schemas.NotificationSettingsResponse.model_validate(settings)
