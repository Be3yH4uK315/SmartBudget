import asyncio
from pathlib import Path
from aiosmtplib import SMTP
from email.message import EmailMessage
import sqlalchemy as sa
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine
from datetime import datetime, timezone
from arq.connections import RedisSettings
from logging import getLogger
from arq.cron import cron
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from jsonschema import validate
import jsonschema
import json
import ssl

from app import (
    settings,
    models,
    schemas,
    logging_config
)

logging_config.setup_logging()
logger = getLogger(__name__)

HEALTH_FILE = Path("/tmp/healthy")

async def touch_health_file():
    """Обновляет файл статуса здоровья воркера."""
    try:
        HEALTH_FILE.touch()
    except Exception as e:
        logger.warning(f"Failed to touch health file: {e}")

async def send_email(ctx, to: str, subject: str, body: str):
    """Задача Arq для отправки email."""
    await touch_health_file()
    logger.info(f"Sending email to {to}")
    
    message = EmailMessage()
    message["From"] = settings.settings.SMTP.SMTP_FROM_EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    tls_context = ssl.create_default_context()
    use_implicit_tls = (settings.settings.SMTP.SMTP_PORT == 465)

    client = SMTP(
        hostname=settings.settings.SMTP.SMTP_HOST,
        port=settings.settings.SMTP.SMTP_PORT,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=60
    )

    try:
        await client.connect()
        if not use_implicit_tls:
            await client.starttls()

        await client.login(settings.settings.SMTP.SMTP_USER, settings.settings.SMTP.SMTP_PASS)
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

async def send_kafka_event(ctx, topic: str, event_data: dict, schema_name: str):
    """Задача Arq для отправки события Kafka."""
    await touch_health_file()
    
    schema = schemas.SCHEMAS_MAP.get(schema_name)
    if not schema:
        logger.error(f"Invalid schema name: {schema_name}")
        return

    try:
        validate(instance=event_data, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        return

    producer: AIOKafkaProducer = ctx.get("kafka_producer")
    if not producer:
        logger.error("Kafka producer not available")
        return

    for attempt in range(3):
        try:
            await producer.send_and_wait(topic, json.dumps(event_data).encode())
            logger.info(f"Kafka event sent to {topic}")
            return
        except KafkaError as e:
            logger.warning(f"Kafka connection error (attempt {attempt+1}/3): {e}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error sending Kafka event (attempt {attempt+1}/3): {e}")
            await asyncio.sleep(1)
    
    logger.error("Failed to send Kafka event after retries")

async def cleanup_sessions(ctx):
    """Задача Arq (Cron) для очистки старых сессий."""
    await touch_health_file()
    
    db_maker: async_sessionmaker[AsyncSession] = ctx.get("db_session_maker")
    if not db_maker:
        logger.error("DB session maker not available for cleanup task")
        return

    async with db_maker() as session:
        try:
            result = await session.execute(
                delete(models.Session).where(
                    or_(
                        models.Session.expires_at < datetime.now(timezone.utc),
                        models.Session.revoked == sa.true()
                    )
                )
            )
            await session.commit()
            count = result.rowcount
            logger.info(f"Cleaned up {count} expired/revoked sessions")
        except Exception as e:
            await session.rollback()
            logger.error(f"Cleanup task failed: {e}", exc_info=True)
            raise

async def on_startup(ctx):
    """Выполняется при старте воркера Arq."""
    logger.info(f"Arq worker starting. Redis: {settings.settings.ARQ.REDIS_URL}")

    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS
        )
        await producer.start()
        ctx["kafka_producer"] = producer
        logger.info("Kafka producer started")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        ctx["kafka_producer"] = None

    try:
        engine = create_async_engine(settings.settings.DB.DB_URL)
        db_maker = async_sessionmaker(engine, expire_on_commit=False)
        ctx["db_engine"] = engine
        ctx["db_session_maker"] = db_maker
        logger.info("DB engine and session maker injected")
    except Exception as e:
        logger.error(f"Failed to create DB engine/session maker: {e}")
        ctx["db_engine"] = None
        ctx["db_session_maker"] = None
    
    await touch_health_file()

async def on_shutdown(ctx):
    """Выполняется при остановке воркера Arq."""
    logger.info("Shutting down Arq worker...")
    
    producer: AIOKafkaProducer = ctx.get("kafka_producer")
    if producer:
        try:
            await producer.stop()
            logger.info("Kafka producer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")

    engine: AsyncEngine = ctx.get("db_engine")
    if engine:
        try:
            await engine.dispose()
            logger.info("DB engine disposed")
        except Exception as e:
            logger.error(f"Error disposing DB engine: {e}")

class WorkerSettings:
    """Настройки для Arq worker."""
    functions = [
        send_email,
        send_kafka_event,
        cleanup_sessions,
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [cron(cleanup_sessions, hour=3, minute=0)]
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    max_tries = 5
    max_jobs = 10