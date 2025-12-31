import logging
from uuid import UUID
from sqlalchemy import select, delete
from app.infrastructure.db.models import OutboxEvent
from app.infrastructure.db.repositories.base import BaseRepository
from app.core.exceptions import InvalidKafkaMessageError
from app.utils.serialization import to_json_dict

logger = logging.getLogger(__name__)

class OutboxRepository(BaseRepository):
    def add_event(self, topic: str, event_data: dict, event_type: str) -> None:
        """Добавляет событие в outbox."""
        try:
            clean_payload = to_json_dict(event_data)
            event = OutboxEvent(
                topic=topic,
                event_type=event_type,
                payload=clean_payload,
                status='pending'
            )
            self.db.add(event)
        except Exception as e:
            logger.error(f"Failed to serialize outbox event: {e}")
            raise InvalidKafkaMessageError("Event serialization failed")

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Получает ожидающие события для отправки в Kafka."""
        query = (
            select(OutboxEvent)
            .where(OutboxEvent.status == 'pending')
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_events(self, event_ids: list[UUID]) -> None:
        """Удаляет успешно отправленные события из outbox."""
        if not event_ids: return
        stmt = delete(OutboxEvent).where(OutboxEvent.event_id.in_(event_ids))
        await self.db.execute(stmt)

    async def handle_failed_event(
        self, 
        event_id: UUID, 
        error_msg: str, 
        max_retries: int = 5
    ) -> None:
        """Обрабатывает неудачное событие, увеличивая счетчик попыток и обновляя статус."""
        event = await self.db.get(OutboxEvent, event_id)
        if event:
            event.retry_count += 1
            event.last_error = error_msg[:512]
            if event.retry_count >= max_retries:
                event.status = 'failed'
            self.db.add(event)