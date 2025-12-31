import logging
import json

from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils.serialization import app_json_serializer

logger = logging.getLogger(__name__)

async def process_outbox_task(ctx) -> None:
    """Читает outbox и отправляет в Kafka."""
    db_session_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")
    if not db_session_maker or not kafka: return

    uow = UnitOfWork(db_session_maker)
    async with uow:
        events = await uow.outbox.get_pending_events(limit=50)
        if not events: return
        
        sent_ids = []
        for event in events:
            try:
                msg_bytes = json.dumps(event.payload, default=app_json_serializer).encode('utf-8')
                key_bytes = str(event.payload.get("transaction_id", "")).encode('utf-8')
                
                if await kafka.send_raw(event.topic, msg_bytes, key=key_bytes):
                    sent_ids.append(event.event_id)
                else:
                    await uow.outbox.handle_failed_event(event.event_id, "Kafka send failed")
            except Exception as e:
                logger.error(f"Error processing event {event.event_id}: {e}")
                await uow.outbox.handle_failed_event(event.event_id, str(e))
        
        await uow.outbox.delete_events(sent_ids)

async def cleanup_sessions_task(ctx):
    # Логика очистки ML сервиса ????
    pass