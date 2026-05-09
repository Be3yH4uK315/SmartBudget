from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.db import models
from app.infrastructure.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """Репозиторий уведомлений."""

    async def create(self, data: dict) -> models.Notification | None:
        """Создает уведомление или возвращает None, если event_id уже существует."""
        statement = (
            pg_insert(models.Notification)
            .values(**data)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(models.Notification)
        )

        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[models.Notification], int]:
        """Получает страницу уведомлений и общее количество."""
        count_statement = select(func.count()).where(
            models.Notification.user_id == user_id,
        )

        if is_read is not None:
            count_statement = count_statement.where(
                models.Notification.is_read == is_read,
            )

        total = await self.db.scalar(count_statement) or 0
        if total == 0:
            return [], 0

        statement = select(models.Notification).where(
            models.Notification.user_id == user_id,
        )

        if is_read is not None:
            statement = statement.where(models.Notification.is_read == is_read)

        statement = (
            statement.order_by(models.Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(statement)

        return list(result.scalars().all()), total

    async def list_paginated(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[models.Notification]:
        """Получает страницу уведомлений без отдельного подсчета total."""
        statement = select(models.Notification).where(
            models.Notification.user_id == user_id,
        )

        if is_read is not None:
            statement = statement.where(models.Notification.is_read == is_read)

        statement = (
            statement.order_by(models.Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(statement)

        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """Считает количество непрочитанных уведомлений пользователя."""
        statement = select(func.count()).where(
            models.Notification.user_id == user_id,
            models.Notification.is_read.is_(False),
        )

        return await self.db.scalar(statement) or 0

    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Помечает уведомление пользователя прочитанным."""
        statement = (
            update(models.Notification)
            .where(
                models.Notification.notification_id == notification_id,
                models.Notification.user_id == user_id,
            )
            .values(
                is_read=True,
                read_at=func.coalesce(
                    models.Notification.read_at,
                    datetime.now(timezone.utc),
                ),
            )
        )

        result = await self.db.execute(statement)

        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Помечает все непрочитанные уведомления пользователя прочитанными."""
        statement = (
            update(models.Notification)
            .where(
                models.Notification.user_id == user_id,
                models.Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone.utc),
            )
        )

        result = await self.db.execute(statement)

        return result.rowcount
