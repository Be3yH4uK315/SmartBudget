from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.utils import serialization, time


class OutboxRepository:
    """Репозиторий outbox-событий."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _build_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> models.OutboxEvent:
        """Создает ORM-модель outbox-события."""
        clean_payload = serialization.recursive_normalize(payload)
        nested_payload = clean_payload.get("payload")
        resolved_event_type = (
            event_type
            or clean_payload.get("event_type")
            or (
                nested_payload.get("event_type")
                if isinstance(nested_payload, dict)
                else None
            )
        )

        if not resolved_event_type:
            raise ValueError("event_type is required for outbox events")

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
        """Добавляет несколько outbox-событий без commit."""
        if not events:
            return

        for event in events:
            self.db.add(
                self._build_event(
                    topic=event["topic"],
                    payload=event.get("payload", event),
                    event_type=event.get("event_type"),
                ),
            )

    def add_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> None:
        """Добавляет одно outbox-событие без commit."""
        self.add_events(
            [
                {
                    "topic": topic,
                    "payload": payload,
                    "event_type": event_type,
                },
            ],
        )

    async def get_pending_events(
        self, limit_amount: int = 100
    ) -> list[models.OutboxEvent]:
        """Получает pending-события, готовые к отправке."""
        result = await self.db.execute(
            select(models.OutboxEvent)
            .where(
                and_(
                    models.OutboxEvent.status == "pending",
                    models.OutboxEvent.retry_count < 5,
                    models.OutboxEvent.next_retry_at <= time.utc_now(),
                ),
            )
            .order_by(models.OutboxEvent.next_retry_at.asc())
            .limit(limit_amount)
            .with_for_update(skip_locked=True),
        )

        return list(result.scalars().all())

    async def delete_events(self, event_ids: list[UUID]) -> None:
        """Удаляет outbox-события по ID."""
        if not event_ids:
            return

        await self.db.execute(
            delete(models.OutboxEvent).where(
                models.OutboxEvent.event_id.in_(event_ids),
            ),
        )

    async def delete_old_failed_events(self, retention_days: int = 7) -> int:
        """Удаляет failed-события старше указанного срока."""
        cutoff_date = time.utc_now() - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(models.OutboxEvent).where(
                and_(
                    models.OutboxEvent.status == "failed",
                    models.OutboxEvent.created_at < cutoff_date,
                ),
            ),
        )

        return result.rowcount or 0
