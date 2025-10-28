import asyncio
from aiosmtplib import send, SMTPException
from email.message import EmailMessage
import sqlalchemy as sa
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from logging import getLogger
from arq.connections import RedisSettings, create_pool
from arq.cron import cron

from .settings import settings
from .models import Session as DBSession
from .dependencies import async_session, engine

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from jsonschema import validate
import jsonschema
import json
from .kafka import SCHEMAS

logger = getLogger(__name__)

# --- Задачи Arq ---
async def send_email_async(ctx, to: str, subject: str, body: str):
    """
    Задача Arq для отправки email.
    'ctx' - это словарь контекста воркера.
    """
    message = EmailMessage()
    message["From"] = settings.smtp_user or "no-reply@example.com"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    logger.info(f"Arq: Пробуем отправить письмо на {to} через {settings.smtp_host}:{settings.smtp_port}")
    
    try:
        await send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_pass or None,
            start_tls=False # В prod => True
        )
        logger.info(f"Arq: Email sent to {to}")
    except SMTPException as e:
        logger.error(f"Arq: SMTP error sending email to {to}: {e}")
        raise

async def send_kafka_event_async(ctx, topic: str, event_data: dict, schema_name: str):
    """
    Задача Arq для отправки события Kafka.
    """
    schema = SCHEMAS.get(schema_name)
    if not schema:
        logger.error(f"Arq: Invalid schema name: {schema_name}")
        return

    try:
        validate(instance=event_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Arq: Invalid event data: {e}")
        return

    producer: AIOKafkaProducer = ctx["kafka_producer"]
    try:
        await producer.send_and_wait(topic, value=json.dumps(event_data).encode('utf-8'))
        logger.info(f"Arq: Event sent to {topic}: {event_data.get('event')}")
    except KafkaConnectionError as e:
        logger.warning(f"Arq: Kafka connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Arq: Kafka send failed: {e}")
        raise

async def cleanup_sessions_async(ctx):
    """
    Задача Arq (Cron) для очистки старых сессий.
    """
    db: AsyncSession = ctx["db_session"]
    async with db() as session:
        try:
            await session.execute(
                delete(DBSession).where(
                    or_(
                        DBSession.expires_at < datetime.now(timezone.utc),
                        DBSession.revoked == sa.true()
                    )
                )
            )
            await session.commit()
            logger.info("Arq: Expired/revoked sessions cleaned up")
        except Exception as e:
            logger.error(f"Arq: Cleanup task failed: {e}")
            await session.rollback()
            raise

# --- Жизненный цикл Воркера ---
async def startup(ctx):
    """
    Выполняется при старте воркера Arq.
    Инициализируем пулы соединений.
    """
    logger.info("Arq Worker starting up...")
    ctx["kafka_producer"] = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers
    )
    await ctx["kafka_producer"].start()
    ctx["db_session"] = async_session 
    logger.info("Arq Worker startup complete.")

async def shutdown(ctx):
    """
    Выполняется при остановке воркера Arq.
    """
    logger.info("Arq Worker shutting down...")
    if "kafka_producer" in ctx:
        await ctx["kafka_producer"].stop()
    await engine.dispose() 
    logger.info("Arq Worker shutdown complete.")

# --- Настройки Воркера ---
functions = [send_email_async, send_kafka_event_async, cleanup_sessions_async]
cron_jobs = [
    cron(
        'app.worker.cleanup_sessions_async', 
        hour=3, 
        minute=0, 
        run_at_startup=False
    )
]

class WorkerSettings:
    """
    Главный класс настроек, который Arq использует для запуска.
    """
    functions = functions
    cron_jobs = cron_jobs
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_url(settings.redis_url) 
    queue_name = settings.arq_queue_name
