import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models

logger = logging.getLogger(__name__)

class NotificationRepository:
    """Репозиторий для операций с таблицей уведомлений."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> models.Notification | None:
        """Создает новое уведомление. Возвращает None, если такой event_id уже есть (защита от дублей)."""
        stmt = (
            pg_insert(models.Notification)
            .values(**data)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(models.Notification)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_paginated(
        self, 
        user_id: UUID, 
        is_read: Optional[bool] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Tuple[List[models.Notification], int]:
        """Получает список уведомлений с пагинацией и общим количеством."""
        count_stmt = select(func.count()).where(models.Notification.user_id == user_id)
        if is_read is not None:
            count_stmt = count_stmt.where(models.Notification.is_read == is_read)
        
        total = await self.db.scalar(count_stmt) or 0

        if total == 0:
            return [], 0

        stmt = select(models.Notification).where(models.Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(models.Notification.is_read == is_read)
            
        stmt = stmt.order_by(models.Notification.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_unread_count(self, user_id: UUID) -> int:
        """Считает количество непрочитанных уведомлений юзера."""
        stmt = select(func.count()).where(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        )
        return await self.db.scalar(stmt) or 0

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Помечает конкретное уведомление как прочитанное."""
        stmt = (
            update(models.Notification)
            .where(
                models.Notification.id == notification_id,
                models.Notification.user_id == user_id,
            )
            .values(
                is_read=True, 
                read_at=func.coalesce(models.Notification.read_at, datetime.now(timezone.utc))
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Помечает все непрочитанные уведомления как прочитанные."""
        stmt = (
            update(models.Notification)
            .where(
                models.Notification.user_id == user_id,
                models.Notification.is_read == False
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone.utc)
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount


class SettingsRepository:
    """Репозиторий для управления настройками пользователя и его email."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> models.UserNotificationSettings | None:
        """Получает настройки по ID пользователя."""
        stmt = select(models.UserNotificationSettings).where(models.UserNotificationSettings.user_id == user_id)
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
        locale: str | None = None,
    ) -> models.UserNotificationSettings:
        """
        Создает профиль настроек или обновляет email, если профиль уже существует.
        Используется при обработке событий из сервиса Auth (регистрация / смена почты).
        """
        values = {
            "user_id": user_id,
            "email": email,
        }
        update_values = {
            "email": email,
            "updated_at": func.now(),
        }
        if locale:
            values["locale"] = locale
            update_values["locale"] = locale

        stmt = pg_insert(models.UserNotificationSettings).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=update_values,
        ).returning(models.UserNotificationSettings)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_settings(self, user_id: UUID, changes: dict) -> models.UserNotificationSettings | None:
        """Обновляет настройки уведомлений (вызывается из API)."""
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
