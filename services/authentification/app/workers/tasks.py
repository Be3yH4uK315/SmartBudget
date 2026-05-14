import asyncio
import logging
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from uuid import UUID

from aiosmtplib import SMTP

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils import network
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

EMAIL_MAX_RETRIES = 3
EMAIL_TIMEOUT_SECONDS = 60
OUTBOX_BATCH_LIMIT = 200
OUTBOX_MAX_RETRIES = 5
FAILED_OUTBOX_RETENTION_DAYS = 7


async def touch_health_file() -> None:
    """Обновляет файл здоровья worker-процесса для Docker/Kubernetes."""
    try:
        HEALTH_FILE.touch()
    except OSError:
        logger.debug("Failed to touch worker health file", exc_info=True)


async def enrich_session_task(
    ctx: dict[str, Any],
    session_id: UUID,
    ip: str,
    user_agent: str,
) -> None:
    """Обогащает сессию данными о местоположении и устройстве."""
    db_session_maker = ctx.get("db_session_maker")
    dadata_client = ctx.get("dadata_client")

    if not db_session_maker:
        logger.warning("Session enrichment skipped: db_session_maker is missing")
        return

    await touch_health_file()

    loop = asyncio.get_running_loop()

    try:
        location_data = await loop.run_in_executor(
            None,
            network.get_location,
            ip,
            dadata_client,
        )
        location = location_data.full
    except Exception as exc:
        logger.error(
            "Error resolving location for IP %s: %s",
            ip,
            exc,
            exc_info=True,
        )
        location = "Unknown"

    try:
        device_name = await loop.run_in_executor(
            None,
            network.parse_device,
            user_agent,
        )
    except Exception as exc:
        logger.error(
            "Error parsing User-Agent: %s",
            exc,
            exc_info=True,
        )
        device_name = "Unknown Device"

    try:
        async with UnitOfWork(db_session_maker) as uow:
            await uow.sessions.update_enrichment_data(
                session_id,
                location,
                device_name,
            )
            await uow.commit()

        logger.info(
            "Enriched session %s: location=%s, device=%s",
            session_id,
            location,
            device_name,
        )

    except Exception as exc:
        logger.error(
            "Failed to enrich session %s: %s",
            session_id,
            exc,
            exc_info=True,
        )


async def send_email_task(
    ctx: dict[str, Any],
    to: str,
    subject: str,
    body: str,
    retry_count: int = 0,
) -> None:
    """Отправляет email с простой retry-логикой."""
    await touch_health_file()

    logger.info(
        "Sending email to %s, attempt %s/%s",
        to,
        retry_count + 1,
        EMAIL_MAX_RETRIES,
    )

    message = EmailMessage()
    message["From"] = settings.SMTP.SMTP_FROM_EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    tls_context = ssl.create_default_context()
    use_implicit_tls = settings.SMTP.SMTP_PORT == 465

    client = SMTP(
        hostname=settings.SMTP.SMTP_HOST,
        port=settings.SMTP.SMTP_PORT,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=EMAIL_TIMEOUT_SECONDS,
    )

    try:
        await client.connect()

        if not use_implicit_tls:
            await client.starttls(tls_context=tls_context)

        await client.login(settings.SMTP.SMTP_USER, settings.SMTP.SMTP_PASS)
        await client.send_message(message)

        logger.info("Email sent successfully to %s", to)

    except asyncio.TimeoutError as exc:
        await _retry_email_or_give_up(
            ctx=ctx,
            to=to,
            subject=subject,
            body=body,
            retry_count=retry_count,
            exc=exc,
        )

    except Exception as exc:
        await _retry_email_or_give_up(
            ctx=ctx,
            to=to,
            subject=subject,
            body=body,
            retry_count=retry_count,
            exc=exc,
        )

    finally:
        try:
            await client.quit()
        except Exception:
            logger.debug("SMTP client quit failed", exc_info=True)


async def _retry_email_or_give_up(
    ctx: dict[str, Any],
    to: str,
    subject: str,
    body: str,
    retry_count: int,
    exc: Exception,
) -> None:
    """Повторяет отправку email или завершает попытки."""
    logger.warning(
        "Failed to send email to %s, attempt %s/%s: %s",
        to,
        retry_count + 1,
        EMAIL_MAX_RETRIES,
        exc,
        exc_info=True,
    )

    if retry_count >= EMAIL_MAX_RETRIES - 1:
        logger.error(
            "Giving up on email to %s after %s attempts",
            to,
            EMAIL_MAX_RETRIES,
        )
        return

    wait_time = 2**retry_count
    await asyncio.sleep(wait_time)

    await send_email_task(
        ctx=ctx,
        to=to,
        subject=subject,
        body=body,
        retry_count=retry_count + 1,
    )


def _message_key(payload: dict[str, Any]) -> bytes | None:
    """Возвращает Kafka message key из payload или envelope."""
    business_payload = payload.get("payload", payload)

    key = (
        business_payload.get("user_id")
        or business_payload.get("email")
        or business_payload.get("new_email")
        or payload.get("event_id")
        or payload.get("idempotency_key")
    )

    return str(key).encode("utf-8") if key else None


async def process_outbox_task(ctx: dict[str, Any]) -> int:
    """Отправляет pending-события из outbox в Kafka."""
    db_session_maker = ctx.get("db_session_maker")
    kafka_producer: KafkaProducerWrapper | None = ctx.get("kafka_producer")

    if not db_session_maker or not kafka_producer:
        logger.warning("Outbox processing skipped: dependencies are missing")
        return 0

    await touch_health_file()

    async with UnitOfWork(db_session_maker) as uow:
        events = await uow.outbox.get_pending_events(limit_amount=OUTBOX_BATCH_LIMIT)

        if not events:
            return 0

        batch_data: list[dict[str, Any]] = []
        events_map = []

        for event in events:
            try:
                message_bytes = to_json_bytes(event.payload)

                batch_data.append(
                    {
                        "topic": event.topic,
                        "value": message_bytes,
                        "key": _message_key(event.payload),
                        "headers": None,
                    }
                )
                events_map.append(event)

            except Exception as exc:
                logger.error(
                    "Serialization error for outbox event %s: %s",
                    event.event_id,
                    exc,
                    exc_info=True,
                )
                event.status = "failed"
                uow.session.add(event)

        if not batch_data:
            await uow.commit()
            return 0

        results = await kafka_producer.send_batch(batch_data)

        successful_ids: list[UUID] = []
        now = datetime.now(timezone.utc)

        for index, success in enumerate(results):
            event = events_map[index]

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
                delay_seconds = 5**event.retry_count
                event.next_retry_at = now + timedelta(seconds=delay_seconds)

            uow.session.add(event)

        if successful_ids:
            await uow.outbox.delete_events(successful_ids)
            logger.info("Processed %s outbox events", len(successful_ids))

        await uow.commit()

        return len(successful_ids)


async def cleanup_sessions_task(ctx: dict[str, Any]) -> None:
    """Удаляет истекшие и отозванные сессии."""
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.warning("Session cleanup skipped: db_session_maker is missing")
        return

    await touch_health_file()

    try:
        async with UnitOfWork(db_session_maker) as uow:
            deleted_count = await uow.sessions.delete_expired_or_revoked()
            await uow.commit()

        if deleted_count > 0:
            logger.info("Cleaned up %s expired/revoked sessions", deleted_count)

    except Exception as exc:
        logger.error("Cleanup sessions failed: %s", exc, exc_info=True)


async def cleanup_failed_outbox_task(ctx: dict[str, Any]) -> None:
    """Удаляет failed outbox-события старше заданного срока хранения."""
    db_session_maker = ctx.get("db_session_maker")
    if not db_session_maker:
        logger.warning("Failed outbox cleanup skipped: db_session_maker is missing")
        return

    await touch_health_file()

    try:
        async with UnitOfWork(db_session_maker) as uow:
            deleted_count = await uow.outbox.delete_old_failed_events(
                retention_days=FAILED_OUTBOX_RETENTION_DAYS,
            )
            await uow.commit()

        if deleted_count > 0:
            logger.info("Cleaned up %s old failed outbox events", deleted_count)

    except Exception as exc:
        logger.error("Cleanup outbox failed: %s", exc, exc_info=True)
