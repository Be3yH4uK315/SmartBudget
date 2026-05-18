from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.db import models
from app.infrastructure.db.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    """Репозиторий настроек уведомлений пользователя."""

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> models.UserNotificationSettings | None:
        """Получает настройки по ID пользователя."""
        result = await self.db.execute(
            select(models.UserNotificationSettings).where(
                models.UserNotificationSettings.user_id == user_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> models.UserNotificationSettings | None:
        """Получает настройки по email без учета регистра."""
        result = await self.db.execute(
            select(models.UserNotificationSettings).where(
                func.lower(models.UserNotificationSettings.email) == email.lower(),
            ),
        )

        return result.scalar_one_or_none()

    async def upsert_profile(
        self,
        user_id: UUID,
        email: str,
        language: str | None = None,
    ) -> models.UserNotificationSettings | None:
        """Создает профиль настроек или обновляет email существующего профиля."""
        values = {
            "user_id": user_id,
            "email": email,
            "language": language or "ru",
        }
        update_values = {
            "email": email,
            "updated_at": func.now(),
        }

        if language:
            update_values["language"] = language

        statement = pg_insert(models.UserNotificationSettings).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=["user_id"],
            set_=update_values,
        ).returning(models.UserNotificationSettings)

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def update_settings(
        self,
        user_id: UUID,
        changes: dict,
    ) -> models.UserNotificationSettings | None:
        """Обновляет настройки уведомлений пользователя."""
        if not changes:
            return await self.get_by_user_id(user_id)

        result = await self.db.execute(
            update(models.UserNotificationSettings)
            .where(models.UserNotificationSettings.user_id == user_id)
            .values(**changes, updated_at=func.now())
            .returning(models.UserNotificationSettings),
        )

        return result.scalar_one_or_none()

    async def add_push_subscription(
        self,
        user_id: UUID,
        subscription: dict,
    ) -> models.UserNotificationSettings | None:
        """Добавляет или обновляет browser push подписку пользователя."""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return None

        endpoint = subscription.get("endpoint")
        subscriptions = [
            item
            for item in (settings.push_subscriptions or [])
            if item.get("endpoint") != endpoint
        ]
        subscriptions.append(subscription)

        return await self.update_settings(
            user_id,
            {
                "push_subscriptions": subscriptions,
                "push_enabled": True,
            },
        )

    async def remove_push_subscriptions_by_session_id(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> models.UserNotificationSettings | None:
        """Удаляет browser push подписки, привязанные к отозванной сессии."""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return None

        session_id_value = str(session_id)
        subscriptions = [
            item
            for item in (settings.push_subscriptions or [])
            if item.get("sessionId") != session_id_value
            and item.get("session_id") != session_id_value
        ]

        if len(subscriptions) == len(settings.push_subscriptions or []):
            return settings

        return await self.update_settings(
            user_id,
            {
                "push_subscriptions": subscriptions,
                "push_enabled": bool(subscriptions),
            },
        )

    async def remove_push_subscription(
        self,
        user_id: UUID,
        endpoint: str,
    ) -> models.UserNotificationSettings | None:
        """Удаляет browser push подписку пользователя."""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return None

        subscriptions = [
            item
            for item in (settings.push_subscriptions or [])
            if item.get("endpoint") != endpoint
        ]

        return await self.update_settings(
            user_id,
            {
                "push_subscriptions": subscriptions,
                "push_enabled": bool(subscriptions),
            },
        )
