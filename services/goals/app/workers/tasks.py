import logging
import asyncio
from pathlib import Path

from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import GoalService
from app.utils.serialization import to_json_str

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file():
    try: HEALTH_FILE.touch()
    except OSError: pass

async def process_outbox_task(ctx) -> None:
    """Параллельная отправка событий."""
    db_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")
    if not db_maker or not kafka: return

    await touch_health_file()

    async with UnitOfWork(db_maker) as uow:
        events = await uow.goals.get_pending_outbox_events(limit=200)
        if not events: return

        send_tasks = []
        event_map = {}

        for i, event in enumerate(events):
            try:
                msg_str = to_json_str(event.payload)
                key_val = event.payload.get("goal_id") or event.payload.get("user_id")
                key = str(key_val).encode('utf-8') if key_val else None
                
                task = kafka.send_event(event.topic, msg_str.encode('utf-8'), key=key)
                send_tasks.append(task)
                event_map[i] = event.event_id
            except Exception as e:
                logger.error(f"Prep error for event {event.event_id}: {e}")

        if not send_tasks:
            return

        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        sent_ids = []
        for i, res in enumerate(results):
            if res is True:
                sent_ids.append(event_map[i])
            else:
                logger.error(f"Failed to send event {event_map[i]}: {res}")

        if sent_ids:
            await uow.goals.delete_outbox_events(sent_ids)

async def cleanup_transactions_task(ctx) -> None:
    """Очистка старых идемпотентных ключей."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker: return
    
    try:
        async with UnitOfWork(db_maker) as uow:
            deleted = await uow.goals.clean_old_processed_transactions(days=30)
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old transaction records")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

async def check_goals_deadlines_task(ctx) -> None:
    """Проверка сроков целей (выполняется ежедневно в 00:00)."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        return

    await touch_health_file()

    try:
        uow = UnitOfWork(db_maker) 
        service = GoalService(uow)
        
        await service.check_deadlines()
        
    except Exception as e:
        logger.error(f"Deadline check failed: {e}", exc_info=True)