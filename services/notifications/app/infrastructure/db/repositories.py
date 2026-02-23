import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import Notification, UserNotificationSettings

class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Optional[Notification]:
        """Создает новое уведомление. Защита от дублей по event_id."""
        new_notification = Notification(**data)
        self.session.add(new_notification)
        try:
            await self.session.commit()
            await self.session.refresh(new_notification)
            return new_notification
        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_paginated_by_user(
        self, user_id: uuid.UUID, is_read: Optional[bool] = None, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Notification], int]:
        """Получает список уведомлений пользователя с пагинацией и общим количеством."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt)
        
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        
        return list(result.all()), total or 0

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Считает количество непрочитанных."""
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, 
            Notification.is_read == False
        )
        return await self.session.scalar(stmt) or 0

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Помечает конкретное уведомление как прочитанное."""
        stmt = update(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        ).values(is_read=True)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Помечает все непрочитанные уведомления юзера как прочитанные."""
        stmt = update(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        ).values(is_read=True)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: uuid.UUID, email: str = "unknown@example.com") -> UserNotificationSettings:
        """Получает настройки, если их нет — создает дефолтные."""
        stmt = select(UserNotificationSettings).where(UserNotificationSettings.user_id == user_id)
        settings = await self.session.scalar(stmt)
        
        if not settings:
            settings = UserNotificationSettings(user_id=user_id, email=email)
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
            
        return settings

    async def update(self, user_id: uuid.UUID, update_data: dict) -> Optional[UserNotificationSettings]:
        """Обновляет настройки пользователя."""
        if not update_data:
            return await self.get_or_create(user_id)
            
        stmt = update(UserNotificationSettings).where(
            UserNotificationSettings.user_id == user_id
        ).values(**update_data).returning(UserNotificationSettings)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()
