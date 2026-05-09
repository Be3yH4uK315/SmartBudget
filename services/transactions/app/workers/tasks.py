import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)
HEALTH_FILE = Path("/tmp/healthy")
MAX_RETRIES = 5


def _message_key(payload: dict[str, Any]) -> bytes | None:
    key = (
        payload.get("transaction_id")
        or payload.get("event_id")
        or payload.get("user_id")
    )
    return str(key).encode("utf-8") if key else None


async def touch_health_file() -> None:
    try:
        HEALTH_FILE.touch()
    except OSError:
        pass


async def run_outbox_loop(ctx) -> None:
    """Бесконечный цикл обработки Outbox с backoff."""
    logger.info("Starting transactions outbox loop")

    while True:
        try:
            processed_count = await process_outbox_task(ctx)
            if processed_count > 0:
                continue

            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info("Transactions outbox loop cancelled")
            break
        except Exception as exc:
            logger.error("Transactions outbox loop error: %s", exc, exc_info=True)
            await asyncio.sleep(5.0)


async def process_outbox_task(ctx) -> int:
    """Обрабатывает пачку outbox-событий."""
    db_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")

    if not db_maker or not kafka:
        return 0

    await touch_health_file()

    async with UnitOfWork(db_maker) as uow:
        events = await uow.outbox.get_pending_events(limit=200)
        if not events:
            return 0

        batch_data: list[dict[str, Any]] = []
        events_map: list[models.OutboxEvent] = []

        for event in events:
            try:
                headers = []
                if event.trace_id:
                    headers.append(("X-Request-ID", event.trace_id.encode("utf-8")))

                batch_data.append(
                    {
                        "topic": event.topic,
                        "value": to_json_bytes(event.payload),
                        "key": _message_key(event.payload),
                        "headers": headers or None,
                    }
                )
                events_map.append(event)
            except Exception as exc:
                logger.error(
                    "Outbox event serialization failed: event_id=%s error=%s",
                    event.event_id,
                    exc,
                    exc_info=True,
                )
                event.retry_count += 1
                event.status = "failed"

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka.send_batch(batch_data)
        successful_ids = []
        now = datetime.now(timezone.utc)

        for event, success in zip(events_map, results, strict=False):
            if success:
                successful_ids.append(event.event_id)
                continue

            event.retry_count += 1
            if event.retry_count >= MAX_RETRIES:
                event.status = "failed"
                logger.error(
                    "Outbox event failed permanently: event_id=%s topic=%s",
                    event.event_id,
                    event.topic,
                )
            else:
                delay = 5 ** event.retry_count
                event.next_retry_at = now + timedelta(seconds=delay)

        if successful_ids:
            await uow.outbox.delete_events(successful_ids)

        await uow.commit()
        return len(successful_ids)
