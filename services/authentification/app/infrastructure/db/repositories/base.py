from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from typing import Any
from sqlalchemy import select, delete, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db import models
from app.utils import serialization

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
        now = datetime.now(timezone.utc)
        
        return {
            "event_id": uuid4(),
            "topic": topic,
            "event_type": event_type,
            "payload": clean_payload,
            "status": "pending",
            "retry_count": 0,
            "created_at": now,
            "next_retry_at": now
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
        now = datetime.now(timezone.utc)
        query = (
            select(models.OutboxEvent)
            .where(
                and_(
                    models.OutboxEvent.status == 'pending',
                    models.OutboxEvent.retry_count < 5,
                    models.OutboxEvent.next_retry_at <= now
                )
            )
            .order_by(models.OutboxEvent.next_retry_at.asc())
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
        """Удаляет события Outbox со статусом 'failed', старше N дней."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stmt = delete(models.OutboxEvent).where(
            and_(
                models.OutboxEvent.status == 'failed',
                models.OutboxEvent.created_at < cutoff_date
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
