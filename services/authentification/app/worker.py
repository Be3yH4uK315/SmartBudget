import asyncio
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
from aiokafka.errors import KafkaConnectionError
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

logging_config.setupLogging()
logger = getLogger(__name__)

async def sendEmail(ctx, to: str, subject: str, body: str):
    """Задача Arq для отправки email. 'ctx' - это словарь контекста воркера."""
    logger.info(f"sendEmail START", extra={"email_to": to})
    
    message = EmailMessage()
    message["From"] = settings.settings.SMTP.SMTP_USER or "no-reply@example.com"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    tlsContext = ssl.create_default_context()

    useUmplicitTls = (settings.settings.SMTP.SMTP_PORT == 465)

    client = SMTP(
        hostname=settings.settings.SMTP.SMTP_HOST,
        port=settings.settings.SMTP.SMTP_PORT,
        use_tls=useUmplicitTls,
        tls_context=tlsContext,
        timeout=60
    )

    try:
        await client.connect()
        if not useUmplicitTls:
            await client.starttls() 

        await client.login(settings.settings.SMTP.SMTP_USER, settings.settings.SMTP.SMTP_PASS)
        await client.send_message(message)
        logger.info(f"Message sent successfully", extra={"email_to": to})

    except Exception as e:
        logger.error(
            f"EMAIL FAILED", 
            extra={"email_to": to, "error": str(e), "error_type": type(e).__name__}
        )
        raise e
    finally:
        try:
            await client.quit()
            logger.debug("Connection closed.", extra={"email_to": to})
        except:
            pass

async def sendKafkaEvent(ctx, topic: str, eventData: dict, schemaName: str):
    """Задача Arq для отправки события Kafka."""
    schema = schemas.SCHEMAS_MAP.get(schemaName)
    if not schema:
        logger.error(f"Arq: Invalid schema name: {schemaName}")
        return

    try:
        validate(instance=eventData, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Arq: Schema validation failed: {e}")
        return

    producer: AIOKafkaProducer = ctx["kafka_producer"]
    if not producer:
        logger.error("Arq: Kafka producer not available")
        return

    for attempt in range(3):
        try:
            await producer.send_and_wait(topic, json.dumps(eventData).encode())
            logger.info(f"Arq: Kafka event sent to {topic}")
            return
        except KafkaConnectionError as e:
            logger.warning(f"Arq: Kafka connection error (attempt {attempt+1}): {e}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Arq: Error sending Kafka event (attempt {attempt+1}): {e}")
            await asyncio.sleep(1)
    raise Exception("Failed to send Kafka event after retries")

async def cleanupSessions(ctx):
    """Задача Arq (Cron) для очистки старых сессий."""
    dbSessionMaker: async_sessionmaker[AsyncSession] = ctx["db_session_maker"]
    if not dbSessionMaker:
        logger.error("Arq: DB session maker not available for cleanup task")
        return

    async with dbSessionMaker() as session:
        try:
            await session.execute(
                delete(models.Session).where(
                    or_(
                        models.Session.expiresAt < datetime.now(timezone.utc),
                        models.Session.revoked == sa.true()
                    )
                )
            )
            await session.commit()
            logger.info("Arq: Expired/revoked sessions cleaned up")
        except Exception as e:
            await session.rollback()
            logger.error(f"Arq: Cleanup task failed: {e}")
            raise

async def onStartup(ctx):
    """Выполняется при старте воркера Arq. Инициализируем пулы соединений."""
    logger.info(f"Arq worker starting. Redis: {settings.settings.ARQ.REDIS_URL}, Queue: {settings.settings.ARQ.ARQ_QUEUE_NAME}")

    try:
        producer = AIOKafkaProducer(bootstrap_servers=settings.settings.KAFKA.KAFKA_BOOTSTRAP_SERVERS)
        await producer.start()
        ctx["kafka_producer"] = producer
        logger.info("Arq: Kafka producer started.")
    except Exception as e:
        logger.error(f"Arq: Failed to start Kafka producer: {e}")
        ctx["kafka_producer"] = None

    try:
        engine = create_async_engine(settings.settings.DB.DB_URL)
        dbSessionMaker = async_sessionmaker(engine, expire_on_commit=False)
        ctx["db_engine"] = engine
        ctx["db_session_maker"] = dbSessionMaker
        logger.info("Arq: DB engine and session maker injected.")
    except Exception as e:
        logger.error(f"Arq: Failed to create DB engine/session maker: {e}")
        ctx["db_engine"] = None
        ctx["db_session_maker"] = None

async def onShutdown(ctx):
    """Выполняется при остановке воркера Arq."""
    logger.info("Shutting down Arq worker...")
    producer: AIOKafkaProducer = ctx.get("kafka_producer")
    if producer:
        await producer.stop()
        logger.info("Arq: Kafka producer stopped.")

    engine: AsyncEngine = ctx.get("db_engine")
    if engine:
        await engine.dispose()
        logger.info("Arq: DB engine disposed.")

class WorkerSettings:
    """Настройки для Arq worker."""
    functions = [
        sendEmail,
        sendKafkaEvent,
        cleanupSessions,
    ]
    on_startup = onStartup
    on_shutdown = onShutdown
    cron_jobs = [cron(cleanupSessions, hour=3, minute=0)]
    queue_name = settings.settings.ARQ.ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.settings.ARQ.REDIS_URL)
    max_tries = 5
    max_jobs = 10