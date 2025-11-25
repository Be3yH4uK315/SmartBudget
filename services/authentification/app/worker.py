import asyncio
from aiosmtplib import SMTP
from email.message import EmailMessage
import sqlalchemy as sa
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from datetime import datetime, timezone
from arq.connections import RedisSettings
from logging import getLogger
from arq.cron import cron
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from jsonschema import validate
import jsonschema
import json
import ssl

from .settings import settings
from .models import Session as DBSession
from .kafka import SCHEMAS
from .middleware import setup_logging

setup_logging()

logger = getLogger(__name__)

async def send_email_async(ctx, to: str, subject: str, body: str):
    """Задача Arq для отправки email. 'ctx' - это словарь контекста воркера."""
    logger.info(f"send_email_async START for {to}")
    
    message = EmailMessage()
    message["From"] = settings.smtp_user or "no-reply@example.com"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    logger.info(f"[STEP 1/5] Using hostname: {settings.smtp_host}")

    tls_context = ssl.create_default_context()

    use_implicit_tls = (settings.smtp_port == 465)

    client = SMTP(
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=60
    )

    try:
        logger.info(f"[STEP 2/5] Connecting to {settings.smtp_host}:{settings.smtp_port} (TLS={use_implicit_tls})...")
        await client.connect()
        logger.info("[STEP 2/5] Connected successfully!")

        if not use_implicit_tls:
            logger.info("[STEP 3/5] Sending STARTTLS command...")
            await client.starttls() 
            logger.info("[STEP 3/5] STARTTLS upgrade success!")
        else:
            logger.info("[STEP 3/5] Skipping STARTTLS (already connected via SSL).")

        logger.info(f"[STEP 4/5] Logging in as {settings.smtp_user}...")
        await client.login(settings.smtp_user, settings.smtp_pass)
        logger.info("[STEP 4/5] Login success!")

        logger.info("[STEP 5/5] Sending message data...")
        await client.send_message(message)
        logger.info(f"[STEP 5/5] Message sent to {to}!")

    except Exception as e:
        logger.error(f"!!! EMAIL FAILED !!! Error: {e}")
        raise e
    finally:
        try:
            await client.quit()
            logger.info("Connection closed.")
        except:
            pass

async def send_kafka_event_async(ctx, topic: str, event_data: dict, schema_name: str):
    """Задача Arq для отправки события Kafka."""
    schema = SCHEMAS.get(schema_name)
    if not schema:
        logger.error(f"Arq: Invalid schema name: {schema_name}")
        return

    try:
        validate(instance=event_data, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Arq: Schema validation failed: {e}")
        return

    producer: AIOKafkaProducer = ctx["kafka_producer"]
    if not producer:
        logger.error("Arq: Kafka producer not available")
        return

    for attempt in range(3):
        try:
            await producer.send_and_wait(topic, json.dumps(event_data).encode())
            logger.info(f"Arq: Kafka event sent to {topic}")
            return
        except KafkaConnectionError as e:
            logger.warning(f"Arq: Kafka connection error (attempt {attempt+1}): {e}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Arq: Error sending Kafka event (attempt {attempt+1}): {e}")
            await asyncio.sleep(1)
    raise Exception("Failed to send Kafka event after retries")

async def cleanup_sessions_async(ctx):
    """Задача Arq (Cron) для очистки старых сессий."""
    db_maker: async_sessionmaker[AsyncSession] = ctx["db_session_maker"]
    async with db_maker() as session:
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
            await session.rollback()
            logger.error(f"Arq: Cleanup task failed: {e}")
            raise

async def on_startup(ctx):
    """Выполняется при старте воркера Arq. Инициализируем пулы соединений."""
    logger.info(f"Arq worker starting. Redis: {settings.redis_url}, Queue: {settings.arq_queue_name}")

    try:
        producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await producer.start()
        ctx["kafka_producer"] = producer
        logger.info("Arq: Kafka producer started.")
    except Exception as e:
        logger.error(f"Arq: Failed to start Kafka producer: {e}")
        ctx["kafka_producer"] = None

    ctx["db_session_maker"] = db_session_maker
    logger.info("Arq: DB session maker injected.")

async def on_shutdown(ctx):
    """Выполняется при остановке воркера Arq."""
    logger.info("Shutting down Arq worker...")
    producer: AIOKafkaProducer = ctx.get("kafka_producer")
    if producer:
        await producer.stop()
        logger.info("Arq: Kafka producer stopped.")
    await engine.dispose()
    logger.info("Arq: DB engine disposed.")

engine = create_async_engine(settings.db_url)
db_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class WorkerSettings:
    """Настройки для Arq worker."""
    functions = [
        send_email_async,
        send_kafka_event_async,
        cleanup_sessions_async,
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    cron_jobs = [cron(cleanup_sessions_async, hour=3, minute=0)]
    queue_name = settings.arq_queue_name
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_tries = 5
    max_jobs = 10