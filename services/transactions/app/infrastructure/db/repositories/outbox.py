from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_request_id
from app.infrastructure.db import models
from app.utils.serialization import to_jsonable


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
        clean_payload = to_jsonable(payload)
        event = models.OutboxEvent(
            event_id=uuid4(),
            topic=topic,
            event_type=event_type
            or clean_payload.get("eventType")
            or clean_payload.get("event_type")
            or clean_payload.get("eventName")
            or "unknown",
            payload=clean_payload,
            status="pending",
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            trace_id=get_request_id(),
            next_retry_at=None,
        )
        return event

    def add_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> None:
        self.db.add(self._build_event(topic, payload, event_type))

    def add_events(self, events: list[dict[str, Any]]) -> None:
        if not events:
            return

        for event in events:
            self.add_event(
                topic=event["topic"],
                payload=event.get("payload", event),
                event_type=event.get("event_type"),
            )

    async def get_pending_events(self, limit: int = 100) -> list[models.OutboxEvent]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(models.OutboxEvent)
            .where(
                models.OutboxEvent.status == "pending",
                or_(
                    models.OutboxEvent.next_retry_at.is_(None),
                    models.OutboxEvent.next_retry_at <= now,
                ),
            )
            .order_by(models.OutboxEvent.created_at.asc())
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
