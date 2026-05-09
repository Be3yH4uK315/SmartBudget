import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select

from app.core.exceptions import InvalidKafkaMessageError
from app.infrastructure.db.models import OutboxEvent
from app.infrastructure.db.repositories.base import BaseRepository
from app.utils.serialization import to_json_dict

logger = logging.getLogger(__name__)


class OutboxRepository(BaseRepository):
    """Репозиторий Outbox-событий."""

    def _build_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> OutboxEvent:
        try:
            clean_payload = to_json_dict(payload)
            resolved_event_type = event_type or clean_payload.get("event_type")
            if not resolved_event_type:
                raise ValueError("event_type is required for outbox events")

            return OutboxEvent(
                topic=topic,
                event_type=resolved_event_type,
                payload=clean_payload,
                status="pending",
            )
        except Exception as exc:
            logger.error("Failed to serialize outbox event: %s", exc)
            raise InvalidKafkaMessageError("Event serialization failed")

    def add_event(
        self,
        topic: str,
        payload: dict[str, Any],
        event_type: str | None = None,
    ) -> None:
        """Добавляет событие в outbox."""
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

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Получает ожидающие события для отправки в Kafka."""
        result = await self.db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def delete_events(self, event_ids: list[UUID]) -> None:
        """Удаляет успешно отправленные события из outbox."""
        if not event_ids:
            return

        await self.db.execute(
            delete(OutboxEvent).where(OutboxEvent.event_id.in_(event_ids))
        )

    async def handle_failed_event(
        self,
        event_id: UUID,
        error_msg: str,
        max_retries: int = 5,
    ) -> None:
        """Обрабатывает неудачное событие, увеличивая счетчик попыток и обновляя статус."""
        event = await self.db.get(OutboxEvent, event_id)
        if not event:
            return

        event.retry_count += 1
        event.last_error = str(error_msg)[:512]
        if event.retry_count >= max_retries:
            logger.error(
                "Event %s reached max retries (%s). Marking as failed.",
                event_id,
                max_retries,
            )
            event.status = "failed"

        self.db.add(event)

    async def delete_old_failed_events(
        self,
        days: int | None = None,
        retention_days: int = 7,
    ) -> int:
        """Удаляет старые failed-события."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=days if days is not None else retention_days
        )
        result = await self.db.execute(
            delete(OutboxEvent).where(
                OutboxEvent.status == "failed",
                OutboxEvent.created_at < cutoff,
            )
        )
        return result.rowcount
