import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.infrastructure.db import models
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.services.service import BudgetService
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

MAX_RETRIES = 5
OUTBOX_BATCH_SIZE = 200
OUTBOX_IDLE_SLEEP_SECONDS = 0.5
OUTBOX_ERROR_SLEEP_SECONDS = 5.0
OUTBOX_RETRY_BASE_SECONDS = 5
REQUEST_ID_HEADER = "X-Request-ID"


def _message_key(payload: dict[str, Any]) -> bytes | None:
    """Возвращает Kafka message key из payload или envelope."""
    business_payload = payload.get("payload", payload)

    key = (
        business_payload.get("budget_id")
        or business_payload.get("user_id")
        or payload.get("event_id")
        or payload.get("idempotency_key")
    )

    return str(key).encode("utf-8") if key else None


async def touch_health_file() -> None:
    """Обновляет health-файл worker-процесса."""
    try:
        HEALTH_FILE.touch(exist_ok=True)
    except OSError:
        logger.debug("Failed to touch worker health file", exc_info=True)


async def run_outbox_loop(ctx: dict[str, Any]) -> None:
    """Запускает постоянный цикл обработки outbox."""
    logger.info("Starting budgets outbox loop")

    while True:
        try:
            processed_count = await process_outbox_task(ctx)
            if processed_count > 0:
                continue

            await asyncio.sleep(OUTBOX_IDLE_SLEEP_SECONDS)

        except asyncio.CancelledError:
            logger.info("Budgets outbox loop cancelled")
            break

        except Exception as exc:
            logger.error(
                "Budgets outbox loop error: %s",
                exc,
                exc_info=True,
            )
            await asyncio.sleep(OUTBOX_ERROR_SLEEP_SECONDS)


async def process_outbox_task(ctx: dict[str, Any]) -> int:
    """Обрабатывает пачку outbox-событий."""
    db_maker = ctx.get("db_session_maker")
    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")

    if not db_maker or not kafka_producer:
        logger.warning("Outbox task skipped: worker context is not initialized")
        return 0

    await touch_health_file()

    async with UnitOfWork(db_maker) as uow:
        events = await uow.outbox.get_pending_events(limitAmount=OUTBOX_BATCH_SIZE)
        if not events:
            return 0

        batch_data, events_map = _build_kafka_batch(events)

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka_producer.send_batch(batch_data)
        successful_ids = _apply_outbox_results(
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


async def renew_monthly_budgets_task(ctx: dict[str, Any]) -> int:
    """Создает бюджеты нового месяца для пользователей с auto-renew."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker:
        logger.warning("Monthly budget renewal skipped: db_session_maker missing")
        return 0

    await touch_health_file()

    try:
        service = BudgetService(UnitOfWork(db_maker))
        created_count = await service.renew_monthly_budgets()

        logger.info(
            "Monthly budgets renewal completed",
            extra={"created_count": created_count},
        )

        return created_count

    except Exception as exc:
        logger.error(
            "Monthly budget renewal failed: %s",
            exc,
            exc_info=True,
        )
        raise


def _build_kafka_batch(
    events: list[models.OutboxEvent],
) -> tuple[list[dict[str, Any]], list[models.OutboxEvent]]:
    """Формирует Kafka batch из outbox events."""
    batch_data: list[dict[str, Any]] = []
    events_map: list[models.OutboxEvent] = []

    for event in events:
        try:
            headers = _build_headers(event)

            batch_data.append(
                {
                    "topic": event.topic,
                    "value": to_json_bytes(event.payload),
                    "key": _message_key(event.payload),
                    "headers": headers or None,
                },
            )
            events_map.append(event)

        except Exception as exc:
            logger.error(
                "Outbox event serialization failed: event_id=%s error=%s",
                event.event_id,
                exc,
                exc_info=True,
            )
            _mark_event_failed(event)

    return batch_data, events_map


def _build_headers(event: models.OutboxEvent) -> list[tuple[str, bytes]]:
    """Формирует Kafka headers для outbox event."""
    headers: list[tuple[str, bytes]] = []

    if event.trace_id:
        headers.append((REQUEST_ID_HEADER, event.trace_id.encode("utf-8")))

    return headers


def _apply_outbox_results(
    events: list[models.OutboxEvent],
    results: list[bool],
) -> list:
    """Применяет результаты отправки Kafka batch к outbox events."""
    successful_ids = []
    now = datetime.now(timezone.utc)

    for event, success in zip(events, results, strict=False):
        if success:
            successful_ids.append(event.event_id)
            continue

        _schedule_retry_or_fail(event, now)

    return successful_ids


def _schedule_retry_or_fail(
    event: models.OutboxEvent,
    now: datetime,
) -> None:
    """Планирует повторную отправку outbox event или помечает его failed."""
    event.retry_count += 1

    if event.retry_count >= MAX_RETRIES:
        event.status = "failed"
        logger.error(
            "Outbox event failed permanently: event_id=%s topic=%s",
            event.event_id,
            event.topic,
        )
        return

    delay = OUTBOX_RETRY_BASE_SECONDS**event.retry_count
    event.next_retry_at = now + timedelta(seconds=delay)

    logger.warning(
        "Outbox event scheduled for retry",
        extra={
            "event_id": str(event.event_id),
            "topic": event.topic,
            "retry_count": event.retry_count,
            "next_retry_at": event.next_retry_at.isoformat(),
        },
    )


def _mark_event_failed(event: models.OutboxEvent) -> None:
    """Помечает outbox event failed после ошибки сериализации."""
    event.retry_count += 1
    event.status = "failed"
