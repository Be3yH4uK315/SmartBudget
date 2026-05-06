from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.db import models
from app.infrastructure.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """Репозиторий для операций с таблицей уведомлений."""

    async def create(self, data: dict) -> models.Notification | None:
        """Создает уведомление. Возвращает None, если event_id уже есть."""
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
        is_read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[models.Notification], int]:
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

    async def list_paginated(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[models.Notification]:
        """Получает страницу уведомлений без отдельного подсчета total."""
        stmt = select(models.Notification).where(models.Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(models.Notification.is_read == is_read)

        stmt = stmt.order_by(models.Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """Считает количество непрочитанных уведомлений пользователя."""
        stmt = select(func.count()).where(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False,
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
                read_at=func.coalesce(
                    models.Notification.read_at,
                    datetime.now(timezone.utc),
                ),
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
                models.Notification.is_read == False,
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
