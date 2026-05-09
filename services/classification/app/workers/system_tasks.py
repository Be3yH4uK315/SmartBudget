import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.db.models import OutboxEvent
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/worker_healthy")

OUTBOX_BATCH_SIZE = 500
OUTBOX_IDLE_SLEEP_SECONDS = 1.0
OUTBOX_BUSY_SLEEP_SECONDS = 0.1
OUTBOX_ERROR_SLEEP_SECONDS = 5.0
OUTBOX_RETRY_BASE_SECONDS = 5
OUTBOX_MAX_RETRY_DELAY_SECONDS = 3600
OUTBOX_MAX_RETRIES = 5
FAILED_EVENTS_RETENTION_DAYS = 7


async def run_outbox_processor(ctx: dict[str, Any]) -> None:
    """Запускает постоянный цикл обработки outbox."""
    logger.info("Starting outbox processor loop")

    while True:
        try:
            await touch_health_file()

            processed_count = await process_outbox_task(ctx)
            if processed_count == 0:
                await asyncio.sleep(OUTBOX_IDLE_SLEEP_SECONDS)
            else:
                await asyncio.sleep(OUTBOX_BUSY_SLEEP_SECONDS)

        except asyncio.CancelledError:
            logger.info("Outbox loop cancelled")
            break

        except Exception as exc:
            logger.error(
                "Outbox loop critical error: %s",
                exc,
                exc_info=True,
            )
            await asyncio.sleep(OUTBOX_ERROR_SLEEP_SECONDS)


async def process_outbox_task(ctx: dict[str, Any]) -> int:
    """Обрабатывает одну пачку outbox-событий."""
    db_maker = ctx.get("db_session_maker")
    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")

    if not db_maker or not kafka_producer:
        logger.warning("Outbox task skipped: worker context is not initialized")
        return 0

    await touch_health_file()

    async with UnitOfWork(db_maker) as uow:
        events = await uow.outbox.get_pending_events(limit=OUTBOX_BATCH_SIZE)
        if not events:
            return 0

        batch_data, events_map = await _build_kafka_batch(
            events=events,
            uow=uow,
        )

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka_producer.send_batch(batch_data)
        successful_ids = await _apply_kafka_results(
            uow=uow,
            events=events_map,
            results=results,
        )

        if successful_ids:
            await uow.outbox.delete_events(successful_ids)

        await uow.commit()

        logger.info(
            "Outbox batch processed",
            extra={
                "events_count": len(events),
                "sent_count": len(successful_ids),
                "failed_count": len(events_map) - len(successful_ids),
            },
        )

        return len(successful_ids)


async def cleanup_sessions_task(ctx: dict[str, Any]) -> None:
    """Удаляет старые failed outbox events."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        logger.warning("Cleanup task skipped: db_session_maker is missing")
        return

    logger.info("Running cleanup task")

    async with UnitOfWork(db_maker) as uow:
        deleted_count = await uow.outbox.delete_old_failed_events(
            days=FAILED_EVENTS_RETENTION_DAYS,
        )

    logger.info(
        "Cleanup deleted %s old failed outbox events",
        deleted_count,
    )


async def touch_health_file() -> None:
    """Обновляет health-файл worker-процесса."""
    try:
        HEALTH_FILE.touch(exist_ok=True)
    except OSError:
        logger.debug("Failed to touch worker health file", exc_info=True)


async def _build_kafka_batch(
    events: list[OutboxEvent],
    uow: UnitOfWork,
) -> tuple[list[dict[str, Any]], list[OutboxEvent]]:
    """Формирует Kafka batch из outbox events."""
    batch_data: list[dict[str, Any]] = []
    events_map: list[OutboxEvent] = []
    now = datetime.now(timezone.utc)

    for event in events:
        if _should_skip_by_retry_delay(event, now):
            continue

        try:
            batch_data.append(
                {
                    "topic": event.topic,
                    "value": to_json_bytes(event.payload),
                    "key": _message_key(event.payload),
                    "headers": None,
                },
            )
            events_map.append(event)

        except Exception as exc:
            logger.error(
                "Serialization error for outbox event %s: %s",
                event.event_id,
                exc,
                exc_info=True,
            )
            await uow.outbox.handle_failed_event(
                event.event_id,
                f"Serialization: {exc}",
                max_retries=OUTBOX_MAX_RETRIES,
            )

    return batch_data, events_map


def _should_skip_by_retry_delay(
    event: OutboxEvent,
    now: datetime,
) -> bool:
    """Проверяет, нужно ли пропустить событие до истечения retry delay."""
    if event.retry_count <= 0:
        return False

    required_delay = OUTBOX_RETRY_BASE_SECONDS ** event.retry_count
    required_delay = min(required_delay, OUTBOX_MAX_RETRY_DELAY_SECONDS)

    return bool(
        event.created_at
        and now < event.created_at + timedelta(seconds=required_delay)
    )


def _message_key(payload: dict[str, Any]) -> bytes | None:
    """Возвращает Kafka message key из payload."""
    key = (
        payload.get("transaction_id")
        or payload.get("event_id")
        or payload.get("user_id")
    )

    return str(key).encode("utf-8") if key else None


async def _apply_kafka_results(
    uow: UnitOfWork,
    events: list[OutboxEvent],
    results: list[bool],
) -> list[UUID]:
    """Применяет результаты отправки Kafka batch к outbox events."""
    successful_ids: list[UUID] = []

    for event, success in zip(events, results, strict=False):
        if success:
            successful_ids.append(event.event_id)
            continue

        logger.warning(
            "Failed to send outbox event %s to %s",
            event.event_id,
            event.topic,
        )
        await uow.outbox.handle_failed_event(
            event.event_id,
            "Kafka send failed",
            max_retries=OUTBOX_MAX_RETRIES,
        )

    return successful_ids
