import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import GoalService
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file() -> None:
    try:
        HEALTH_FILE.touch()
    except OSError:
        pass

async def run_outbox_loop(ctx) -> None:
    """Бесконечный цикл обработки Outbox с Backoff."""
    logger.info("Starting Outbox Loop")

    while True:
        try:
            processed_count = await process_outbox_batch(ctx)

            if processed_count > 0:
                continue

            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            logger.info("Outbox loop cancelled")
            break

        except Exception as e:
            logger.error(
                "Error in outbox loop: %s",
                e,
                exc_info=True,
            )
            await asyncio.sleep(5.0)

async def process_outbox_batch(ctx) -> int:
    """Обрабатывает пачку событий."""
    db_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")

    if not db_maker or not kafka:
        return 0

    await touch_health_file()

    async with UnitOfWork(db_maker) as uow:
        events = await uow.goals.get_pending_outbox_events(limit=200)

        if not events:
            return 0

        batch_data = []
        events_map = []

        for event in events:
            try:
                msg_bytes = to_json_bytes(event.payload)

                key_val = (
                    event.payload.get("goal_id")
                    or event.payload.get("user_id")
                )
                key = (
                    str(key_val).encode("utf-8")
                    if key_val
                    else None
                )

                headers = []
                if event.trace_id:
                    headers.append(
                        ("X-Request-ID", event.trace_id.encode("utf-8"))
                    )

                batch_data.append(
                    {
                        "topic": event.topic,
                        "value": msg_bytes,
                        "key": key,
                        "headers": headers,
                    }
                )
                events_map.append(event)

            except Exception as e:
                logger.error(
                    "Serialization error for event %s: %s",
                    event.event_id,
                    e,
                )
                event.status = "failed"
                event.retry_count += 1

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka.send_batch(batch_data)

        successful_ids = []
        res_idx = 0
        now = datetime.now(timezone.utc)

        for event in events_map:
            if event.status == "failed":
                continue

            success = results[res_idx]
            res_idx += 1

            if success:
                successful_ids.append(event.event_id)
            else:
                event.retry_count += 1

                if event.retry_count >= 5:
                    event.status = "failed"
                    logger.error(
                        "Event %s failed permanently after 5 retries",
                        event.event_id,
                    )
                else:
                    delay = 5 ** event.retry_count
                    event.next_retry_at = now + timedelta(seconds=delay)

        if successful_ids:
            await uow.goals.delete_outbox_events(successful_ids)

        await uow.commit()
        return len(successful_ids)

async def cleanup_transactions_task(ctx) -> None:
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        return

    try:
        async with UnitOfWork(db_maker) as uow:
            await uow.goals.ensure_current_partition()
            await uow.goals.drop_old_partitions(retention_months=3)

        logger.info("Partition maintenance completed")

    except Exception as e:
        logger.error(
            "Partition maintenance failed: %s",
            e,
        )

async def check_goals_deadlines_task(ctx) -> None:
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        return

    await touch_health_file()

    try:
        async with UnitOfWork(db_maker) as uow:
            service = GoalService(uow)
            await service.check_deadlines()

    except Exception as e:
        logger.error(
            "Deadline check failed: %s",
            e,
            exc_info=True,
        )
