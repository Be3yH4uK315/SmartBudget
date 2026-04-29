import logging
from datetime import datetime
from hashlib import sha256
from typing import Any, Mapping, Protocol
from uuid import UUID

from arq import ArqRedis

from app.core import config, exceptions, metrics
from app.core.registry import EVENT_REGISTRY
from app.domain.enums import NotificationServiceType
from app.domain.schemas import api as api_schemas, kafka as k_schemas
from app.infrastructure.db import uow
from app.api.websockets import ws_manager

logger = logging.getLogger(__name__)


class _NotificationRow(Protocol):
    id: UUID
    created_at: datetime
    title_key: str
    type: str
    is_read: bool
    message_key: str
    props: Mapping[str, Any] | None
    service: str


class _NotificationSettingsRow(Protocol):
    notifications_enabled: bool
    push_enabled: bool
    disabled_services: list[str] | None

AUTH_NOTIFICATION_EVENT_MAP = {
    "user.login": "auth.device.new_login",
    "user.password_changed": "auth.password.changed",
}

FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_WINDOW_SECONDS = 30 * 60
SUSPICIOUS_ACTIVITY_COOLDOWN_SECONDS = 60 * 60


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
                email=event.payload.email,
                locale=self._normalize_locale(event.payload.locale or event.payload.language),
            )
            await self.uow.commit()
            logger.info("Synchronized profile for user %s from Auth event.", event.user_id)

    async def process_auth_outbox_event(
        self,
        event: k_schemas.AuthOutboxEvent,
        event_id: UUID,
        timestamp: datetime,
    ) -> None:
        """Обрабатывает фактические события auth outbox и маппит их в уведомления."""
        await self._sync_auth_profile(event)

        if event.event_type == "user.login_failed":
            await self._handle_failed_login(event, event_id, timestamp)
            return

        notification_event_name = AUTH_NOTIFICATION_EVENT_MAP.get(event.event_type)
        if not notification_event_name or not event.user_id:
            return

        await self.process_incoming_event(
            k_schemas.IncomingNotificationEvent(
                event_id=event_id,
                event_name=notification_event_name,
                user_id=event.user_id,
                payload={},
                timestamp=timestamp,
            )
        )

    async def process_incoming_event(self, event: k_schemas.IncomingNotificationEvent) -> None:
        """Основная обработка бизнес-событий из платформы (Budget, Goals, etc.)."""
        route_config = EVENT_REGISTRY.get(event.event_name)
        if not route_config:
            logger.warning("Event '%s' not found in registry. Ignored.", event.event_name)
            return

        props = self._filter_props(route_config.message_key, route_config.props, event.payload)

        async with self.uow:
            settings = await self.uow.settings.get_by_user_id(event.user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(event.user_id, self._placeholder_email(event.user_id))
                await self.uow.commit()

            if not settings.notifications_enabled:
                logger.info("User %s disabled all notifications. Ignored.", event.user_id)
                return

            if route_config.service.value in (settings.disabled_services or []):
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
                "props": props or {},
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
            if (
                "EMAIL" in channels
                and config.settings.SMTP.SMTP_ENABLED
                and not self._is_placeholder_email(settings.email)
            ):
                await self.arq_pool.enqueue_job(
                    "send_email_task",
                    user_id=event.user_id,
                    email=settings.email,
                    locale=settings.locale,
                    title_key=route_config.title_key,
                    message_key=route_config.message_key,
                    props=props or {}
                )
                metrics.BACKGROUND_TASKS_ENQUEUED.labels(task_name="send_email_task").inc()

            if "PUSH" in channels and settings.push_subscriptions:
                await self.arq_pool.enqueue_job(
                    "send_push_task",
                    user_id=event.user_id,
                    push_subscriptions=settings.push_subscriptions,
                    locale=settings.locale,
                    title_key=route_config.title_key,
                    message_key=route_config.message_key,
                    props=props or {}
                )
                metrics.BACKGROUND_TASKS_ENQUEUED.labels(task_name="send_push_task").inc()

        ws_payload = self._notification_to_response(notification).model_dump(
            by_alias=True,
            mode="json",
            exclude_none=True,
        )
        ws_event = {"event_type": "new_notification", "data": ws_payload}
        await ws_manager.send_personal_message(str(event.user_id), ws_event)

    # --- REST API METHODS ---

    async def get_paginated_notifications(
        self, user_id: UUID, is_read: bool | None, limit: int, offset: int
    ) -> list[api_schemas.NotificationResponse]:
        """Получает историю уведомлений для UI."""
        async with self.uow:
            notifications, _ = await self.uow.notifications.get_paginated(user_id, is_read, limit, offset)

        return [self._notification_to_response(n) for n in notifications]

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
                settings = await self.uow.settings.upsert_profile(user_id, self._placeholder_email(user_id))
                await self.uow.commit()
        return self._settings_to_response(settings)

    async def update_settings(
        self, user_id: UUID, request: api_schemas.NotificationSettingsUpdate
    ) -> api_schemas.NotificationSettingsResponse:
        async with self.uow:
            changes = self._settings_update_to_changes(request)
            settings = await self.uow.settings.get_by_user_id(user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(user_id, self._placeholder_email(user_id))
            if not settings.notifications_enabled:
                changes["push_enabled"] = False
            settings = await self.uow.settings.update_settings(user_id, changes)
            if not settings:
                raise exceptions.InvalidNotificationDataError("Notification settings were not created")
            await self.uow.commit()
        return self._settings_to_response(settings)

    async def update_notifications_status(
        self,
        user_id: UUID,
        notifications_status: bool,
    ) -> api_schemas.NotificationSettingsResponse:
        changes = {"notifications_enabled": notifications_status}
        if not notifications_status:
            changes["push_enabled"] = False

        async with self.uow:
            settings = await self.uow.settings.update_settings(user_id, changes)
            if not settings:
                settings = await self.uow.settings.upsert_profile(user_id, self._placeholder_email(user_id))
                settings = await self.uow.settings.update_settings(user_id, changes)
            if not settings:
                raise exceptions.InvalidNotificationDataError("Notification settings were not created")
            await self.uow.commit()
        return self._settings_to_response(settings)

    async def subscribe_push(
        self,
        user_id: UUID,
        subscription: api_schemas.WebPushSubscription,
    ) -> dict:
        async with self.uow:
            settings = await self.uow.settings.get_by_user_id(user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(user_id, self._placeholder_email(user_id))
            updated = await self.uow.settings.add_push_subscription(
                user_id,
                subscription.model_dump(by_alias=True, exclude_none=True),
            )
            if not updated:
                raise exceptions.InvalidNotificationDataError("Notification settings were not created")
            await self.uow.commit()

        return {
            "success": True,
            "subscriptionsCount": len(updated.push_subscriptions or []),
        }

    async def unsubscribe_push(
        self,
        user_id: UUID,
        endpoint: str,
    ) -> dict:
        async with self.uow:
            settings = await self.uow.settings.get_by_user_id(user_id)
            if not settings:
                settings = await self.uow.settings.upsert_profile(user_id, self._placeholder_email(user_id))
            updated = await self.uow.settings.remove_push_subscription(user_id, endpoint)
            if not updated:
                raise exceptions.InvalidNotificationDataError("Notification settings were not created")
            await self.uow.commit()

        return {
            "success": True,
            "subscriptionsCount": len(updated.push_subscriptions or []),
        }

    def _notification_to_response(
        self,
        notification: _NotificationRow,
    ) -> api_schemas.NotificationResponse:
        props = notification.props or None
        return api_schemas.NotificationResponse(
            id=notification.id,
            date=notification.created_at,
            title_key=notification.title_key,
            type=notification.type,
            is_read=notification.is_read,
            message_key=notification.message_key,
            props=props,
            service=notification.service,
        )

    def _settings_to_response(
        self,
        settings: _NotificationSettingsRow,
    ) -> api_schemas.NotificationSettingsResponse:
        disabled = set(settings.disabled_services or [])
        return api_schemas.NotificationSettingsResponse(
            notifications_status=settings.notifications_enabled,
            push_status=settings.push_enabled,
            goals=NotificationServiceType.GOALS.value not in disabled,
            transactions=NotificationServiceType.TRANSACTIONS.value not in disabled,
            budget=api_schemas.BudgetNotificationSettings(
                total_limit=NotificationServiceType.BUDGET.value not in disabled,
                categories_limit=NotificationServiceType.LIMIT.value not in disabled,
            ),
        )

    def _settings_update_to_changes(
        self,
        request: api_schemas.NotificationSettingsUpdate,
    ) -> dict[str, bool | list[str]]:
        disabled_services: list[str] = []
        if not request.goals:
            disabled_services.append(NotificationServiceType.GOALS.value)
        if not request.transactions:
            disabled_services.append(NotificationServiceType.TRANSACTIONS.value)
        if not request.budget.total_limit:
            disabled_services.append(NotificationServiceType.BUDGET.value)
        if not request.budget.categories_limit:
            disabled_services.append(NotificationServiceType.LIMIT.value)

        return {
            "push_enabled": request.push_status,
            "disabled_services": disabled_services,
        }

    def _filter_props(
        self,
        message_key: str,
        expected: tuple[str, ...] | list[str] | None,
        payload: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        if expected is None:
            return None

        missing = [key for key in expected if key not in payload]
        if missing:
            raise ValueError(f"Missing props for {message_key}: {', '.join(missing)}")

        return {key: payload[key] for key in expected}

    def _placeholder_email(self, user_id: UUID) -> str:
        return f"{user_id}@unknown.smartbudget.local"

    def _is_placeholder_email(self, email: str) -> bool:
        return email.endswith("@unknown.smartbudget.local")

    def _normalize_locale(self, locale: str | None) -> str | None:
        if locale in {"ru", "en"}:
            return locale
        return None

    async def _sync_auth_profile(self, event: k_schemas.AuthOutboxEvent) -> None:
        if not event.user_id:
            return

        email = event.new_email or event.email
        locale = self._normalize_locale(event.locale or event.language)
        if not email and not locale:
            return

        async with self.uow:
            current = await self.uow.settings.get_by_user_id(event.user_id)
            profile_email = email
            if not profile_email and current:
                profile_email = current.email
            if not profile_email:
                profile_email = self._placeholder_email(event.user_id)

            await self.uow.settings.upsert_profile(
                user_id=event.user_id,
                email=profile_email,
                locale=locale,
            )
            await self.uow.commit()
            logger.info("Synchronized auth profile for user %s from %s.", event.user_id, event.event_type)

    async def _handle_failed_login(
        self,
        event: k_schemas.AuthOutboxEvent,
        event_id: UUID,
        timestamp: datetime,
    ) -> None:
        if not event.email:
            logger.info("Auth failed login event without email ignored.")
            return

        if not self.arq_pool:
            logger.info("Failed login event ignored because Redis is unavailable.")
            return

        normalized_email = event.email.strip().lower()
        ip = (event.ip or "unknown").strip() or "unknown"
        key_suffix = self._failed_login_key_suffix(normalized_email, ip)

        processed_key = f"notifications:security:failed-login-event:{event_id}"
        processed = await self.arq_pool.set(
            processed_key,
            "1",
            ex=FAILED_LOGIN_WINDOW_SECONDS,
            nx=True,
        )
        if not processed:
            logger.info("Duplicate failed login event %s ignored.", event_id)
            return

        counter_key = f"notifications:security:failed-login:{key_suffix}"
        attempts = await self.arq_pool.incr(counter_key)
        await self.arq_pool.expire(counter_key, FAILED_LOGIN_WINDOW_SECONDS)

        if attempts < FAILED_LOGIN_THRESHOLD:
            logger.info(
                "Failed login below suspicious threshold: %s/%s.",
                attempts,
                FAILED_LOGIN_THRESHOLD,
            )
            return

        cooldown_key = f"notifications:security:suspicious-sent:{key_suffix}"
        should_send = await self.arq_pool.set(
            cooldown_key,
            "1",
            ex=SUSPICIOUS_ACTIVITY_COOLDOWN_SECONDS,
            nx=True,
        )
        if not should_send:
            logger.info("Suspicious activity notification suppressed by cooldown.")
            return

        async with self.uow:
            settings = await self.uow.settings.get_by_email(normalized_email)

        if not settings:
            logger.info("Failed login for unknown notification profile ignored.")
            return

        await self.process_incoming_event(
            k_schemas.IncomingNotificationEvent(
                event_id=event_id,
                event_name="auth.activity.suspicious",
                user_id=settings.user_id,
                payload={},
                timestamp=timestamp,
            )
        )

    def _failed_login_key_suffix(self, email: str, ip: str) -> str:
        return sha256(f"{email}|{ip}".encode("utf-8")).hexdigest()
