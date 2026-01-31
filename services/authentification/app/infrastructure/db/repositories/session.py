from datetime import datetime
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy import select, update, delete, and_, or_
from app.infrastructure.db import models
from app.infrastructure.db.repositories.base import BaseRepository
from app.utils import time

class SessionRepository(BaseRepository):
    """Репозиторий для операций с сессиями."""

    def create(self, session: models.Session) -> models.Session:
        """Создает новую сессию."""
        self.db.add(session)
        return session

    async def get_by_fingerprint(self, fingerprint: str) -> models.Session | None:
        """Находит активную сессию по fingerprint."""
        query = select(models.Session).where(
            and_(
                models.Session.refresh_fingerprint == fingerprint,
                models.Session.revoked == sa.false(),
                models.Session.expires_at > time.utc_now(),
            )
        ).with_for_update()
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_fingerprint(
        self, 
        session: models.Session, 
        new_fingerprint: str,
        new_expires_at: datetime
    ) -> None:
        """Обновляет fingerprint и срок действия (при refresh)."""
        session.refresh_fingerprint = new_fingerprint
        session.expires_at = new_expires_at
        self.db.add(session)
    
    async def update_last_activity(self, session_id: UUID, last_activity: datetime):
        """Обновляет время последней активности."""
        stmt = (
            update(models.Session)
            .where(models.Session.session_id == session_id)
            .values(last_activity=last_activity)
        )
        await self.db.execute(stmt)

    async def update_enrichment_data(self, session_id: UUID, location: str, device_name: str) -> None:
        """Обновляет обогащенные данные сессии (локация + устройство)."""
        stmt = (
            update(models.Session)
            .where(models.Session.session_id == session_id)
            .values(location=location, device_name=device_name)
        )
        await self.db.execute(stmt)

    async def revoke_by_fingerprint(self, user_id: UUID, fingerprint: str) -> None:
        """Отзывает сессию по fingerprint."""
        await self.db.execute(
            update(models.Session)
            .where(
                and_(
                    models.Session.user_id == user_id,
                    models.Session.refresh_fingerprint == fingerprint,
                )
            )
            .values(revoked=True)
        )

    async def get_all_active(self, user_id: UUID) -> list[models.Session]:
        """Получает все активные сессии пользователя."""
        query = (
            select(models.Session)
            .where(
                and_(
                    models.Session.user_id == user_id,
                    models.Session.revoked == sa.false(),
                    models.Session.expires_at > time.utc_now()
                )
            )
            .order_by(models.Session.last_activity.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke_by_id(self, user_id: UUID, session_id: UUID) -> None:
        """Отзывает конкретную сессию."""
        await self.db.execute(
            update(models.Session)
            .where(
                and_(
                    models.Session.session_id == session_id,
                    models.Session.user_id == user_id,
                )
            )
            .values(revoked=True)
        )

    async def revoke_all_except(self, user_id: UUID, current_fingerprint: str) -> list[UUID]:
        """Отзывает все сессии, кроме текущей."""
        result = await self.db.execute( 
            update(models.Session) 
            .where( 
                and_( 
                    models.Session.user_id == user_id, 
                    models.Session.refresh_fingerprint != current_fingerprint, 
                    models.Session.revoked == sa.false(), 
                ) 
            ) 
            .values(revoked=True) 
            .returning(models.Session.session_id) 
        )
        return list(result.scalars().all())

    async def revoke_all_for_user(self, user_id: UUID) -> list[UUID]:
        """Отзывает все сессии пользователя."""
        result = await self.db.execute(
            update(models.Session)
            .where( 
                and_( 
                    models.Session.user_id == user_id, 
                    models.Session.revoked == sa.false()
                )
            ) 
            .values(revoked=True) 
            .returning(models.Session.session_id) 
        )
        return list(result.scalars().all())

    async def delete_expired_or_revoked(self) -> int:
        """Удаляет сессии, которые истекли по времени или были отозваны."""
        result = await self.db.execute(
            delete(models.Session).where(
                or_(
                    models.Session.expires_at < time.utc_now(),
                    models.Session.revoked == sa.true()
                )
            )
        )
        return result.rowcount

    async def get_active_by_id(self, session_id: UUID) -> models.Session | None:
        """Ищет сессию по ID, проверяя, что она жива."""
        query = select(models.Session).where(
            and_(
                models.Session.session_id == session_id,
                models.Session.revoked == sa.false(),
                models.Session.expires_at > time.utc_now(),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
