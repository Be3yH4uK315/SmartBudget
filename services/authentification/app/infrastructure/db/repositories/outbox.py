from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.utils import serialization, time


class OutboxRepository:
    """Репозиторий Outbox-событий."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> models.OutboxEvent:
        clean_payload = serialization.recursive_normalize(payload)
        resolved_event_type = (
            event_type
            or clean_payload.get("event_type")
            or clean_payload.get("event")
            or "unknown"
        )
        now = time.utc_now()

        return models.OutboxEvent(
            event_id=uuid4(),
            topic=topic,
            event_type=resolved_event_type,
            payload=clean_payload,
            status="pending",
            retry_count=0,
            created_at=now,
            next_retry_at=now,
        )

    def add_events(self, events: list[dict[str, Any]]) -> None:
        if not events:
            return

        for event in events:
            self.db.add(
                self._build_event(
                    event["topic"],
                    event.get("payload", event),
                    event.get("event_type"),
                )
            )

    def add_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> None:
        self.add_events(
            [
                {
                    "topic": topic,
                    "payload": payload,
                    "event_type": event_type,
                }
            ]
        )

    async def get_pending_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        now = time.utc_now()
        result = await self.db.execute(
            select(models.OutboxEvent)
            .where(
                and_(
                    models.OutboxEvent.status == "pending",
                    models.OutboxEvent.retry_count < 5,
                    models.OutboxEvent.next_retry_at <= now,
                )
            )
            .order_by(models.OutboxEvent.next_retry_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def delete_events(self, event_ids: list[UUID]) -> None:
        if not event_ids:
            return

        await self.db.execute(
            delete(models.OutboxEvent).where(
                models.OutboxEvent.event_id.in_(event_ids),
            )
        )

    async def delete_old_failed_events(self, retention_days: int = 7) -> int:
        cutoff_date = time.utc_now() - timedelta(days=retention_days)
        result = await self.db.execute(
            delete(models.OutboxEvent).where(
                and_(
                    models.OutboxEvent.status == "failed",
                    models.OutboxEvent.created_at < cutoff_date,
                )
            )
        )
        return result.rowcount
