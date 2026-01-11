import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from typing import Any

import sqlalchemy as sa
from sqlalchemy import and_, delete, or_, select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.domain.schemas import api as schemas
from app.utils import serialization

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Базовый репозиторий. 
    Содержит общую логику и методы для Outbox паттерна.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _prepare_outbox_event(self, topic: str, event_data: dict) -> dict:
        """Приводит входные данные к формату для вставки в outbox_events."""
        payload = event_data.get("payload", event_data)
        
        event_type = event_data.get("event_type")
        if not event_type and isinstance(payload, dict):
             event_type = payload.get("event_type", "unknown")
             if event_type == "unknown":
                 event_type = payload.get("event", "unknown")
        
        clean_payload = serialization.recursive_normalize(payload)
        
        return {
            "event_id": uuid4(),
            "topic": topic,
            "event_type": event_type,
            "payload": clean_payload,
            "status": "pending",
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc)
        }
    
    async def add_outbox_events(self, events: list[dict[str, Any]]) -> None:
        """Массовое добавление событий в Outbox."""
        if not events:
            return

        clean_events = [
            self._prepare_outbox_event(e["topic"], e.get("payload", e))
            for e in events
        ]
        
        stmt = insert(models.OutboxEvent).values(clean_events)
        await self.db.execute(stmt)

    async def add_outbox_event(self, topic: str, event_data: dict) -> None:
        """Добавление одного события."""
        await self.add_outbox_events([{"topic": topic, "payload": event_data}])
    
    async def get_pending_outbox_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        """Получает события для отправки (только pending и retry_count < 5)."""
        query = (
            select(models.OutboxEvent)
            .where(
                and_(
                    models.OutboxEvent.status == 'pending',
                    models.OutboxEvent.retry_count < 5
                )
            )
            .order_by(models.OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_outbox_events(self, event_ids: list[UUID]) -> None:
        """Удаляет отправленные события."""
        if not event_ids:
            return
        stmt = delete(models.OutboxEvent).where(models.OutboxEvent.event_id.in_(event_ids))
        await self.db.execute(stmt)

    async def delete_old_failed_events(self, retention_days: int = 7) -> int:
        """
        Удаляет события Outbox со статусом 'failed', которые старше указанного кол-ва дней.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = delete(models.OutboxEvent).where(
            and_(
                models.OutboxEvent.status == 'failed',
                models.OutboxEvent.created_at < cutoff_date
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount

class UserRepository(BaseRepository):
    """Репозиторий для операций с пользователями."""

    async def get_by_email(self, email: str) -> models.User | None:
        """Получает пользователя по email."""
        result = await self.db.execute(
            select(models.User).where(models.User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> models.User | None:
        """Получает пользователя по ID."""
        return await self.db.get(models.User, user_id)

    async def get_role_by_id(self, user_id: UUID) -> int:
        """Получает только роль пользователя по ID."""
        result = await self.db.execute(
            select(models.User.role).where(models.User.user_id == user_id)
        )
        val = result.scalar_one_or_none()
        return val if val is not None else schemas.UserRole.USER.value

    def create(self, user: models.User) -> models.User:
        """Создает нового пользователя (не делает commit)."""
        self.db.add(user)
        return user

    async def update_last_login(self, user_id: UUID) -> None:
        """Обновляет время последнего входа."""
        await self.db.execute(
            update(models.User)
            .where(models.User.user_id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )

    def update_password(self, user: models.User, new_hash: str) -> None:
        """Обновляет хэш пароля."""
        user.password_hash = new_hash
        user.updated_at = datetime.now(timezone.utc)
        self.db.add(user)


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
                models.Session.expires_at > datetime.now(timezone.utc),
            )
        )
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
                )
            )
            .order_by(models.Session.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke_by_id(self, user_id: UUID, session_id: UUID) -> None:
        """Отзывает конкретную сессию по ее ID."""
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

    async def revoke_all_except(self, user_id: UUID, current_fingerprint: str) -> int:
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
        )
        return result.rowcount or 0

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Отзывает все сессии пользователя."""
        await self.db.execute(
            update(models.Session)
            .where(models.Session.user_id == user_id)
            .values(revoked=True)
        )

    async def delete_expired_or_revoked(self) -> int:
        """Удаляет сессии, которые истекли по времени или были отозваны."""
        result = await self.db.execute(
            delete(models.Session).where(
                or_(
                    models.Session.expires_at < datetime.now(timezone.utc),
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
                models.Session.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()