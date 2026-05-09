from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.db import models
from app.infrastructure.db.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    """Репозиторий для управления настройками пользователя и его email."""

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> models.UserNotificationSettings | None:
        """Получает настройки по ID пользователя."""
        stmt = select(models.UserNotificationSettings).where(
            models.UserNotificationSettings.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> models.UserNotificationSettings | None:
        """Получает настройки по email без учета регистра."""
        stmt = select(models.UserNotificationSettings).where(
            func.lower(models.UserNotificationSettings.email) == email.lower()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_profile(
        self,
        user_id: UUID,
        email: str,
        language: str | None = None,
    ) -> models.UserNotificationSettings:
        """
        Создает профиль настроек или обновляет email, если профиль уже существует.
        Используется при обработке событий из сервиса Auth.
        """
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

        stmt = pg_insert(models.UserNotificationSettings).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_=update_values,
        ).returning(models.UserNotificationSettings)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_settings(
        self,
        user_id: UUID,
        changes: dict,
    ) -> models.UserNotificationSettings | None:
        """Обновляет настройки уведомлений."""
        if not changes:
            return await self.get_by_user_id(user_id)

        stmt = (
            update(models.UserNotificationSettings)
            .where(models.UserNotificationSettings.user_id == user_id)
            .values(**changes, updated_at=func.now())
            .returning(models.UserNotificationSettings)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_push_subscription(
        self,
        user_id: UUID,
        subscription: dict,
    ) -> models.UserNotificationSettings | None:
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

    async def remove_push_subscription(
        self,
        user_id: UUID,
        endpoint: str,
    ) -> models.UserNotificationSettings | None:
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
