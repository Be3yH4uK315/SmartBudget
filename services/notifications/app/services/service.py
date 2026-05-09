import logging
from datetime import datetime
from hashlib import sha256
from typing import Any, Mapping, Protocol
from uuid import UUID

from arq import ArqRedis

from app.api.websockets import ws_manager
from app.core import config, exceptions, metrics
from app.core.registry import EVENT_REGISTRY, EventRouteConfig
from app.domain.enums import NotificationServiceType
from app.domain.schemas import api as api_schemas
from app.domain.schemas import kafka as kafka_schemas
from app.infrastructure.db import uow

logger = logging.getLogger(__name__)

AUTH_NOTIFICATION_EVENT_MAP = {
    "user.login": "auth.device.new_login",
    "user.password_changed": "auth.password.changed",
}

FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_WINDOW_SECONDS = 30 * 60
SUSPICIOUS_ACTIVITY_COOLDOWN_SECONDS = 60 * 60
PLACEHOLDER_EMAIL_DOMAIN = "@unknown.smartbudget.local"


class _NotificationRow(Protocol):
    """Минимальный контракт ORM-объекта уведомления."""

    notification_id: UUID
    created_at: datetime
    title_key: str
    notification_type: str
    is_read: bool
    message_key: str
    props: Mapping[str, Any] | None
    service: str


class _NotificationSettingsRow(Protocol):
    """Минимальный контракт ORM-объекта настроек уведомлений."""

    user_id: UUID
    email: str
    notifications_enabled: bool
    push_enabled: bool
    email_enabled: bool
    language: str
    disabled_services: list[str] | None
    push_subscriptions: list[dict[str, Any]] | None


class NotificationService:
    """Бизнес-логика маршрутизации и управления уведомлениями."""

    def __init__(
        self,
        unit_of_work: uow.UnitOfWork,
        arq_pool: ArqRedis | None = None,
    ) -> None:
        self.uow = unit_of_work
        self.arq_pool = arq_pool

    async def process_auth_event(self, event: kafka_schemas.AuthUserEvent) -> None:
        """Синхронизирует профиль пользователя из auth event."""
        async with self.uow:
            await self.uow.settings.upsert_profile(
                user_id=event.user_id,
                email=event.payload.email,
                language=self._normalize_language(event.payload.language),
            )
            await self.uow.commit()

        logger.info("Synchronized profile for user %s from auth event", event.user_id)

    async def process_auth_outbox_event(
        self,
        event: kafka_schemas.AuthOutboxEvent,
        event_id: UUID,
        timestamp: datetime,
    ) -> None:
        """Обрабатывает auth outbox event и при необходимости создает уведомление."""
        await self._sync_auth_profile(event)

        if event.event_type == "user.login_failed":
            await self._handle_failed_login(event, event_id, timestamp)
            return

        notification_event_name = AUTH_NOTIFICATION_EVENT_MAP.get(event.event_type)
        if not notification_event_name or not event.user_id:
            return

        await self.process_incoming_event(
            kafka_schemas.IncomingNotificationEvent(
                event_id=event_id,
                event_type=notification_event_name,
                user_id=event.user_id,
                payload={},
                timestamp=timestamp,
            ),
        )

    async def process_incoming_event(
        self,
        event: kafka_schemas.IncomingNotificationEvent,
    ) -> None:
        """Обрабатывает входящее бизнес-событие платформы."""
        route_config = EVENT_REGISTRY.get(event.event_type)
        if not route_config:
            logger.warning(
                "Event %s not found in registry. Ignored",
                event.event_type,
            )
            return

        props = self._filter_props(
            message_key=route_config.message_key,
            expected=route_config.props,
            payload=event.payload,
        )

        async with self.uow:
            settings = await self._get_or_create_settings_in_uow(event.user_id)

            if self._should_skip_notification(event.user_id, route_config, settings):
                return

            channels = self._resolve_channels(route_config, settings)

            notification = await self._create_notification_in_uow(
                event=event,
                route_config=route_config,
                props=props,
            )

            if not notification:
                logger.info("Duplicate event %s ignored", event.event_id)
                return

            await self.uow.commit()

        metrics.NOTIFICATIONS_CREATED_TOTAL.labels(
            service=route_config.service.value,
            notification_type=route_config.notification_type.value,
        ).inc()

        await self._enqueue_background_deliveries(
            user_id=event.user_id,
            settings=settings,
            route_config=route_config,
            channels=channels,
            props=props or {},
        )
        await self._send_websocket_notification(event.user_id, notification)

    async def get_paginated_notifications(
        self,
        user_id: UUID,
        is_read: bool | None,
        limit: int,
        offset: int,
    ) -> list[api_schemas.NotificationResponse]:
        """Получает историю уведомлений пользователя для UI."""
        async with self.uow:
            notifications = await self.uow.notifications.list_paginated(
                user_id,
                is_read,
                limit,
                offset,
            )

        return [
            self._notification_to_response(notification)
            for notification in notifications
        ]

    async def get_unread_count(self, user_id: UUID) -> dict:
        """Возвращает количество непрочитанных уведомлений."""
        async with self.uow:
            count = await self.uow.notifications.get_unread_count(user_id)

        return {"unreadCount": count}

    async def mark_as_read(
        self,
        user_id: UUID,
        notification_id: UUID,
    ) -> dict:
        """Отмечает одно уведомление прочитанным."""
        async with self.uow:
            success = await self.uow.notifications.mark_as_read(
                notification_id,
                user_id,
            )

            if not success:
                raise exceptions.NotificationNotFoundError(
                    "Notification not found or already read",
                )

            await self.uow.commit()

        return {
            "success": True,
            "notificationId": str(notification_id),
        }

    async def mark_all_as_read(self, user_id: UUID) -> dict:
        """Отмечает все уведомления пользователя прочитанными."""
        async with self.uow:
            updated_count = await self.uow.notifications.mark_all_as_read(user_id)
            await self.uow.commit()

        return {
            "success": True,
            "updatedCount": updated_count,
        }

    async def get_settings(
        self,
        user_id: UUID,
    ) -> api_schemas.NotificationSettingsResponse:
        """Возвращает настройки уведомлений пользователя."""
        async with self.uow:
            settings = await self._get_or_create_settings_in_uow(user_id)
            await self.uow.commit()

        return self._settings_to_response(settings)

    async def update_settings(
        self,
        user_id: UUID,
        request: api_schemas.NotificationSettingsUpdate,
    ) -> api_schemas.NotificationSettingsResponse:
        """Обновляет настройки уведомлений пользователя."""
        async with self.uow:
            changes = self._settings_update_to_changes(request)

            settings = await self._get_or_create_settings_in_uow(user_id)
            if not settings.notifications_enabled:
                changes["push_enabled"] = False

            updated_settings = await self.uow.settings.update_settings(
                user_id,
                changes,
            )

            if not updated_settings:
                raise exceptions.InvalidNotificationDataError(
                    "Notification settings were not created",
                )

            await self.uow.commit()

        return self._settings_to_response(updated_settings)

    async def update_notifications_status(
        self,
        user_id: UUID,
        notifications_status: bool,
    ) -> api_schemas.NotificationSettingsResponse:
        """Включает или выключает уведомления пользователя."""
        changes: dict[str, bool] = {
            "notifications_enabled": notifications_status,
        }

        if not notifications_status:
            changes["push_enabled"] = False

        async with self.uow:
            settings = await self.uow.settings.update_settings(user_id, changes)

            if not settings:
                await self._get_or_create_settings_in_uow(user_id)
                settings = await self.uow.settings.update_settings(user_id, changes)

            if not settings:
                raise exceptions.InvalidNotificationDataError(
                    "Notification settings were not created",
                )

            await self.uow.commit()

        return self._settings_to_response(settings)

    async def subscribe_push(
        self,
        user_id: UUID,
        subscription: api_schemas.WebPushSubscription,
    ) -> dict:
        """Сохраняет browser push подписку пользователя."""
        async with self.uow:
            await self._get_or_create_settings_in_uow(user_id)

            updated = await self.uow.settings.add_push_subscription(
                user_id,
                subscription.model_dump(
                    by_alias=True,
                    exclude_none=True,
                ),
            )

            if not updated:
                raise exceptions.InvalidNotificationDataError(
                    "Notification settings were not created",
                )

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
        """Удаляет browser push подписку пользователя."""
        async with self.uow:
            await self._get_or_create_settings_in_uow(user_id)

            updated = await self.uow.settings.remove_push_subscription(
                user_id,
                endpoint,
            )

            if not updated:
                raise exceptions.InvalidNotificationDataError(
                    "Notification settings were not created",
                )

            await self.uow.commit()

        return {
            "success": True,
            "subscriptionsCount": len(updated.push_subscriptions or []),
        }

    async def _get_or_create_settings_in_uow(
        self,
        user_id: UUID,
    ) -> _NotificationSettingsRow:
        """Возвращает настройки пользователя или создает placeholder-профиль."""
        settings = await self.uow.settings.get_by_user_id(user_id)
        if settings:
            return settings

        created_settings = await self.uow.settings.upsert_profile(
            user_id,
            self._placeholder_email(user_id),
        )

        if not created_settings:
            raise exceptions.InvalidNotificationDataError(
                "Notification settings were not created",
            )

        return created_settings

    async def _create_notification_in_uow(
        self,
        event: kafka_schemas.IncomingNotificationEvent,
        route_config: EventRouteConfig,
        props: dict[str, Any] | None,
    ) -> _NotificationRow | None:
        """Создает in-app уведомление внутри текущего UnitOfWork."""
        notification_data = {
            "event_id": event.event_id,
            "user_id": event.user_id,
            "service": route_config.service.value,
            "notification_type": route_config.notification_type.value,
            "title_key": route_config.title_key,
            "message_key": route_config.message_key,
            "props": props or {},
        }

        async with self.uow.make_savepoint():
            return await self.uow.notifications.create(notification_data)

    async def _enqueue_background_deliveries(
        self,
        user_id: UUID,
        settings: _NotificationSettingsRow,
        route_config: EventRouteConfig,
        channels: set[str],
        props: dict[str, Any],
    ) -> None:
        """Ставит email/push доставки в ARQ."""
        if not self.arq_pool:
            return

        if self._should_send_email(channels, settings):
            await self.arq_pool.enqueue_job(
                "send_email_task",
                user_id=user_id,
                email=settings.email,
                language=settings.language,
                title_key=route_config.title_key,
                message_key=route_config.message_key,
                props=props,
            )
            metrics.BACKGROUND_TASKS_ENQUEUED.labels(
                task_name="send_email_task",
            ).inc()

        if self._should_send_push(channels, settings):
            await self.arq_pool.enqueue_job(
                "send_push_task",
                user_id=user_id,
                push_subscriptions=settings.push_subscriptions,
                language=settings.language,
                title_key=route_config.title_key,
                message_key=route_config.message_key,
                props=props,
            )
            metrics.BACKGROUND_TASKS_ENQUEUED.labels(
                task_name="send_push_task",
            ).inc()

    async def _send_websocket_notification(
        self,
        user_id: UUID,
        notification: _NotificationRow,
    ) -> None:
        """Отправляет уведомление в активные WebSocket-соединения пользователя."""
        ws_payload = self._notification_to_response(notification).model_dump(
            by_alias=True,
            mode="json",
            exclude_none=True,
        )
        ws_event = {
            "event_type": "new_notification",
            "data": ws_payload,
        }

        await ws_manager.send_personal_message(str(user_id), ws_event)

    def _should_skip_notification(
        self,
        user_id: UUID,
        route_config: EventRouteConfig,
        settings: _NotificationSettingsRow,
    ) -> bool:
        """Проверяет пользовательские настройки перед созданием уведомления."""
        if not settings.notifications_enabled:
            logger.info("User %s disabled all notifications. Ignored", user_id)
            return True

        disabled_services = settings.disabled_services or []
        if route_config.service.value in disabled_services:
            logger.info(
                "User %s disabled notifications for %s. Ignored",
                user_id,
                route_config.service.value,
            )
            return True

        return False

    @staticmethod
    def _resolve_channels(
        route_config: EventRouteConfig,
        settings: _NotificationSettingsRow,
    ) -> set[str]:
        """Определяет итоговый набор каналов доставки."""
        channels = set(route_config.default_channels)

        if not settings.push_enabled:
            channels.discard("PUSH")

        if not settings.email_enabled:
            channels.discard("EMAIL")

        return channels

    @staticmethod
    def _should_send_email(
        channels: set[str],
        settings: _NotificationSettingsRow,
    ) -> bool:
        """Проверяет, нужно ли отправлять email."""
        return (
            "EMAIL" in channels
            and config.settings.SMTP.SMTP_ENABLED
            and not NotificationService._is_placeholder_email(settings.email)
        )

    @staticmethod
    def _should_send_push(
        channels: set[str],
        settings: _NotificationSettingsRow,
    ) -> bool:
        """Проверяет, нужно ли отправлять push."""
        return "PUSH" in channels and bool(settings.push_subscriptions)

    def _notification_to_response(
        self,
        notification: _NotificationRow,
    ) -> api_schemas.NotificationResponse:
        """Преобразует notification row в API response."""
        props = self._props_to_response(notification.props)

        return api_schemas.NotificationResponse(
            notification_id=notification.notification_id,
            created_at=notification.created_at,
            title_key=notification.title_key,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            message_key=notification.message_key,
            props=props,
            service=notification.service,
        )

    @staticmethod
    def _props_to_response(
        props: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Преобразует props из snake_case в camelCase для ответа API."""
        if not props:
            return None

        return {
            api_schemas.to_camel(key): value
            for key, value in props.items()
        }

    @staticmethod
    def _settings_to_response(
        settings: _NotificationSettingsRow,
    ) -> api_schemas.NotificationSettingsResponse:
        """Преобразует настройки пользователя в API response."""
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

    @staticmethod
    def _settings_update_to_changes(
        request: api_schemas.NotificationSettingsUpdate,
    ) -> dict[str, bool | list[str]]:
        """Преобразует API request настроек в изменения для БД."""
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

    @staticmethod
    def _filter_props(
        message_key: str,
        expected: tuple[str, ...] | list[str] | None,
        payload: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        """Фильтрует payload по ожидаемым props из registry."""
        if expected is None:
            return None

        missing = [key for key in expected if key not in payload]
        if missing:
            raise ValueError(
                f"Missing props for {message_key}: {', '.join(missing)}",
            )

        return {
            key: payload[key]
            for key in expected
        }

    @staticmethod
    def _placeholder_email(user_id: UUID) -> str:
        """Возвращает placeholder email для пользователя без email."""
        return f"{user_id}{PLACEHOLDER_EMAIL_DOMAIN}"

    @staticmethod
    def _is_placeholder_email(email: str) -> bool:
        """Проверяет, является ли email placeholder-адресом."""
        return email.endswith(PLACEHOLDER_EMAIL_DOMAIN)

    @staticmethod
    def _normalize_language(language: str | None) -> str | None:
        """Нормализует язык пользователя."""
        if language in {"ru", "en"}:
            return language

        return None

    async def _sync_auth_profile(self, event: kafka_schemas.AuthOutboxEvent) -> None:
        """Синхронизирует notification profile из auth outbox event."""
        if not event.user_id:
            return

        email = event.new_email or event.email
        language = self._normalize_language(event.language)

        if not email and not language:
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
                language=language,
            )
            await self.uow.commit()

        logger.info(
            "Synchronized auth profile for user %s from %s",
            event.user_id,
            event.event_type,
        )

    async def _handle_failed_login(
        self,
        event: kafka_schemas.AuthOutboxEvent,
        event_id: UUID,
        timestamp: datetime,
    ) -> None:
        """Обрабатывает failed login и создает suspicious activity при пороге."""
        if not event.email:
            logger.info("Auth failed login event without email ignored")
            return

        if not self.arq_pool:
            logger.info("Failed login event ignored because Redis is unavailable")
            return

        normalized_email = event.email.strip().lower()
        ip = (event.ip or "unknown").strip() or "unknown"
        key_suffix = self._failed_login_key_suffix(normalized_email, ip)

        if not await self._mark_failed_login_event_processed(event_id):
            logger.info("Duplicate failed login event %s ignored", event_id)
            return

        attempts = await self._increment_failed_login_counter(key_suffix)
        if attempts < FAILED_LOGIN_THRESHOLD:
            logger.info(
                "Failed login below suspicious threshold: %s/%s",
                attempts,
                FAILED_LOGIN_THRESHOLD,
            )
            return

        if not await self._acquire_suspicious_activity_cooldown(key_suffix):
            logger.info("Suspicious activity notification suppressed by cooldown")
            return

        async with self.uow:
            settings = await self.uow.settings.get_by_email(normalized_email)

        if not settings:
            logger.info("Failed login for unknown notification profile ignored")
            return

        await self.process_incoming_event(
            kafka_schemas.IncomingNotificationEvent(
                event_id=event_id,
                event_type="auth.activity.suspicious",
                user_id=settings.user_id,
                payload={},
                timestamp=timestamp,
            ),
        )

    async def _mark_failed_login_event_processed(self, event_id: UUID) -> bool:
        """Помечает failed login event как обработанный в Redis."""
        if not self.arq_pool:
            return False

        processed_key = f"notifications:security:failed-login-event:{event_id}"
        processed = await self.arq_pool.set(
            processed_key,
            "1",
            ex=FAILED_LOGIN_WINDOW_SECONDS,
            nx=True,
        )

        return bool(processed)

    async def _increment_failed_login_counter(self, key_suffix: str) -> int:
        """Увеличивает счетчик failed login попыток."""
        if not self.arq_pool:
            return 0

        counter_key = f"notifications:security:failed-login:{key_suffix}"
        attempts = await self.arq_pool.incr(counter_key)
        await self.arq_pool.expire(counter_key, FAILED_LOGIN_WINDOW_SECONDS)

        return int(attempts)

    async def _acquire_suspicious_activity_cooldown(self, key_suffix: str) -> bool:
        """Создает cooldown ключ для suspicious activity уведомления."""
        if not self.arq_pool:
            return False

        cooldown_key = f"notifications:security:suspicious-sent:{key_suffix}"
        should_send = await self.arq_pool.set(
            cooldown_key,
            "1",
            ex=SUSPICIOUS_ACTIVITY_COOLDOWN_SECONDS,
            nx=True,
        )

        return bool(should_send)

    @staticmethod
    def _failed_login_key_suffix(email: str, ip: str) -> str:
        """Возвращает хешированный ключ failed login счетчика."""
        return sha256(f"{email}|{ip}".encode("utf-8")).hexdigest()
