import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import GoalService
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

OUTBOX_BATCH_LIMIT = 200
OUTBOX_IDLE_SLEEP_SECONDS = 0.5
OUTBOX_ERROR_SLEEP_SECONDS = 5.0
OUTBOX_MAX_RETRIES = 5
PARTITION_RETENTION_MONTHS = 3
REQUEST_ID_HEADER = "X-Request-ID"


async def touch_health_file() -> None:
    """Обновляет health-файл worker-процесса."""
    try:
        HEALTH_FILE.touch()
    except OSError:
        logger.debug("Failed to touch worker health file", exc_info=True)


async def run_outbox_loop(ctx: dict[str, Any]) -> None:
    """Запускает постоянный цикл публикации outbox-событий в Kafka."""
    logger.info("Outbox worker started")

    while True:
        try:
            processed_count = await process_outbox_batch(ctx)

            if processed_count > 0:
                continue

            await asyncio.sleep(OUTBOX_IDLE_SLEEP_SECONDS)

        except asyncio.CancelledError:
            logger.info("Outbox worker stopped")
            break

        except Exception as exc:
            logger.error("Outbox worker failed: %s", exc, exc_info=True)
            await asyncio.sleep(OUTBOX_ERROR_SLEEP_SECONDS)


async def process_outbox_batch(ctx: dict[str, Any]) -> int:
    """Публикует одну пачку pending outbox-событий."""
    db_session_maker = ctx.get("db_session_maker")
    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")

    if not db_session_maker or not kafka_producer:
        logger.warning("Outbox processing skipped: dependencies are missing")
        return 0

    await touch_health_file()

    async with UnitOfWork(db_session_maker) as uow:
        events = await uow.outbox.get_pending_events(limit=OUTBOX_BATCH_LIMIT)

        if not events:
            return 0

        batch_data: list[dict[str, Any]] = []
        events_map = []

        for event in events:
            try:
                batch_data.append(_build_kafka_batch_item(event))
                events_map.append(event)

            except Exception as exc:
                logger.error(
                    "Serialization error for outbox event %s: %s",
                    event.event_id,
                    exc,
                    exc_info=True,
                )
                event.status = "failed"
                event.retry_count += 1

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka_producer.send_batch(batch_data)
        successful_ids = _apply_outbox_results(events_map, results)

        if successful_ids:
            await uow.outbox.delete_events(successful_ids)

        await uow.commit()

        return len(successful_ids)


async def cleanup_transactions_task(ctx: dict[str, Any]) -> None:
    """Создает актуальные партиции и удаляет старые партиции транзакций целей."""
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.warning("Partition maintenance skipped: db_session_maker is missing")
        return

    await touch_health_file()

    try:
        async with UnitOfWork(db_session_maker) as uow:
            await uow.goals.ensure_current_partition()
            await uow.goals.drop_old_partitions(
                retention_months=PARTITION_RETENTION_MONTHS,
            )

        logger.info("Partition maintenance completed")

    except Exception as exc:
        logger.error("Partition maintenance failed: %s", exc, exc_info=True)


async def check_goals_deadlines_task(ctx: dict[str, Any]) -> None:
    """Проверяет сроки целей и создает outbox-события уведомлений."""
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.warning("Deadline check skipped: db_session_maker is missing")
        return

    await touch_health_file()

    try:
        service = GoalService(UnitOfWork(db_session_maker))
        await service.check_deadlines()

        logger.info("Deadline check completed")

    except Exception as exc:
        logger.error("Deadline check failed: %s", exc, exc_info=True)


def _message_key(payload: dict[str, Any]) -> bytes | None:
    """Возвращает Kafka message key из payload или envelope."""
    business_payload = payload.get("payload", payload)
    details = business_payload.get("details", {})

    key = (
        business_payload.get("goal_id")
        or business_payload.get("user_id")
        or details.get("goal_id")
        or details.get("user_id")
        or payload.get("event_id")
        or payload.get("idempotency_key")
    )

    return str(key).encode("utf-8") if key else None


def _build_kafka_batch_item(event) -> dict[str, Any]:
    """Формирует элемент batch-отправки в Kafka из outbox-события."""
    message_bytes = to_json_bytes(event.payload)

    headers: list[tuple[str, bytes]] = []
    if event.trace_id:
        headers.append((REQUEST_ID_HEADER, event.trace_id.encode("utf-8")))

    return {
        "topic": event.topic,
        "value": message_bytes,
        "key": _message_key(event.payload),
        "headers": headers or None,
    }


def _apply_outbox_results(events: list, results: list[bool]) -> list[UUID]:
    """Применяет результаты отправки Kafka batch к outbox-событиям."""
    successful_ids: list[UUID] = []
    now = datetime.now(timezone.utc)

    for event, success in zip(events, results, strict=False):
        if success:
            successful_ids.append(event.event_id)
            continue

        event.retry_count += 1

        if event.retry_count >= OUTBOX_MAX_RETRIES:
            event.status = "failed"
            logger.error(
                "Outbox event %s failed permanently after %s retries",
                event.event_id,
                OUTBOX_MAX_RETRIES,
            )
        else:
            delay_seconds = OUTBOX_MAX_RETRIES**event.retry_count
            event.next_retry_at = now + timedelta(seconds=delay_seconds)

    return successful_ids
