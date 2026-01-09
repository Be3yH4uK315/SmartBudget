from datetime import datetime, timedelta, timezone
import logging
import ssl
from pathlib import Path
from email.message import EmailMessage
from aiosmtplib import SMTP

from app.core.config import settings
from app.infrastructure.db.uow import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducerWrapper
from app.utils.serialization import to_json_bytes

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file():
    """Обновляет файл здоровья для k8s/docker."""
    try: 
        HEALTH_FILE.touch()
    except OSError: 
        pass

async def send_email_task(ctx, to: str, subject: str, body: str):
    """Задача отправки email (выполняется worker-ом)."""
    await touch_health_file()
    logger.info(f"Sending email to {to}")
    
    message = EmailMessage()
    message["From"] = settings.SMTP.SMTP_FROM_EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    tls_context = ssl.create_default_context()
    use_implicit_tls = (settings.SMTP.SMTP_PORT == 465)

    client = SMTP(
        hostname=settings.SMTP.SMTP_HOST,
        port=settings.SMTP.SMTP_PORT,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=60
    )

    try:
        await client.connect()
        if not use_implicit_tls:
            await client.starttls()
        await client.login(settings.SMTP.SMTP_USER, settings.SMTP.SMTP_PASS)
        await client.send_message(message)
        logger.info(f"Email sent successfully to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
        raise
    finally:
        try:
            await client.quit()
        except Exception:
            pass

async def process_outbox_task(ctx) -> int:
    """Параллельная отправка событий из Outbox в Kafka с логикой Retry."""
    db_maker = ctx.get("db_session_maker")
    kafka: KafkaProducerWrapper = ctx.get("kafka_producer")
    
    if not db_maker or not kafka: 
        return 0
    
    await touch_health_file()
    
    async with UnitOfWork(db_maker) as uow:
        events = await uow.users.get_pending_outbox_events(limit=200)
        
        if not events: 
            return 0
        
        batch_data = []
        events_map = []
        now = datetime.now(timezone.utc)

        for event in events:
            if event.retry_count > 0:
                required_delay = 5 ** event.retry_count
                
                if now < event.created_at + timedelta(seconds=required_delay):
                    continue

            try:
                msg_bytes = to_json_bytes(event.payload)
                key_val = event.payload.get("user_id") or event.payload.get("email")
                key = str(key_val).encode('utf-8') if key_val else None
                
                batch_data.append({
                    "topic": event.topic,
                    "value": msg_bytes,
                    "key": key
                })
                events_map.append(event)
            except Exception as e:
                logger.error(f"Serialization error for event {event.event_id}: {e}")
                event.status = 'failed'
                uow.session.add(event)

        if not batch_data:
            await uow.commit() 
            return 0

        results = await kafka.send_batch(batch_data)
        
        successful_ids = []
        
        for i, success in enumerate(results):
            event = events_map[i]
            
            if success:
                successful_ids.append(event.event_id)
            else:
                event.retry_count += 1
                if event.retry_count >= 5:
                    event.status = 'failed'
                    logger.error(f"Event {event.event_id} failed permanently after 5 retries")
                uow.session.add(event)

        if successful_ids:
            await uow.users.delete_outbox_events(successful_ids)
            logger.info(f"Processed {len(successful_ids)} outbox events")

        await uow.commit()
        
        return len(successful_ids)


async def cleanup_sessions_task(ctx) -> None:
    """Очистка истекших и отозванных сессий."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker: return
    
    await touch_health_file()

    try:
        async with UnitOfWork(db_maker) as uow:
            deleted = await uow.sessions.delete_expired_or_revoked()
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired/revoked sessions")
    except Exception as e:
        logger.error(f"Cleanup sessions failed: {e}")

async def cleanup_failed_outbox_task(ctx) -> None:
    """Очистка событий, которые окончательно упали (failed) и старше 7 дней."""
    db_maker = ctx.get("db_session_maker")
    if not db_maker: return
    
    await touch_health_file()

    try:
        async with UnitOfWork(db_maker) as uow:
            deleted_count = await uow.users.delete_old_failed_events(retention_days=7)
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old failed outbox events")
                await uow.commit()
    except Exception as e:
        logger.error(f"Cleanup outbox failed: {e}")