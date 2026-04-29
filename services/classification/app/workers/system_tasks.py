import asyncio
from datetime import datetime, timezone, timedelta
import logging
import json
from pathlib import Path

from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils.serialization import app_json_serializer

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/worker_healthy")

async def run_outbox_processor(ctx):
    """Читает outbox и отправляет в Kafka."""
    logger.info("Starting Outbox Processor Loop...")
    while True:
        try:
            try:
                HEALTH_FILE.touch()
            except OSError:
                pass

            processed_count = await process_outbox_task(ctx)
            if processed_count == 0:
                await asyncio.sleep(1.0)
            else:
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Outbox loop cancelled")
            break
        except Exception as e:
            logger.error(f"Outbox loop critical error: {e}", exc_info=True)
            await asyncio.sleep(5)

async def process_outbox_task(ctx) -> int:
    """Читает пачку событий и отправляет в Kafka."""
    db_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")
    
    if not db_maker or not kafka:
        return 0

    try:
        HEALTH_FILE.touch()
    except OSError:
        pass

    async with UnitOfWork(db_maker) as uow:
        events = await uow.outbox.get_pending_events(limit=500)
        
        if not events: 
            return 0
        
        batch_kafka_data = []
        events_map = []
        now = datetime.now(timezone.utc)
        
        for event in events:
            if event.retry_count > 0:
                required_delay = 5 ** event.retry_count
                required_delay = min(required_delay, 3600)
                if event.created_at and now < event.created_at + timedelta(seconds=required_delay):
                    continue

            try:
                msg_bytes = json.dumps(event.payload, default=app_json_serializer).encode('utf-8')
                key_val = event.payload.get("transaction_id")
                key_bytes = str(key_val).encode('utf-8') if key_val else None
                
                batch_kafka_data.append({
                    "topic": event.topic,
                    "value": msg_bytes,
                    "key": key_bytes
                })
                events_map.append(event)
                
            except Exception as e:
                logger.error(f"Serialization error for event {event.event_id}: {e}")
                await uow.outbox.handle_failed_event(event.event_id, f"Serialization: {str(e)}")
        
        if not batch_kafka_data:
            await uow.commit()
            return 0

        results = await kafka.send_batch(batch_kafka_data)
        
        successful_ids = []
        
        for i, success in enumerate(results):
            event = events_map[i]
            
            if success:
                successful_ids.append(event.event_id)
            else:
                logger.warning(f"Failed to send event {event.event_id} to {event.topic}")
                await uow.outbox.handle_failed_event(event.event_id, "Kafka send failed")

        if successful_ids:
            await uow.outbox.delete_events(successful_ids)
            logger.debug(f"Processed {len(successful_ids)} outbox events")
            
        await uow.commit()
        return len(successful_ids)

async def cleanup_sessions_task(ctx):
    """Очистка старых данных (failed events старше 7 дней)."""
    db_maker = ctx.get("db_session_maker")
    logger.info("Running cleanup task...")
    
    async with UnitOfWork(db_maker) as uow:
        deleted_count = await uow.outbox.delete_old_failed_events(days=7)
        logger.info(f"Cleanup: Deleted {deleted_count} old failed outbox events.")