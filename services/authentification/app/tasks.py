import asyncio
from celery import Celery
from celery.schedules import crontab
from aiosmtplib import send, SMTPException
from email.message import EmailMessage
import sqlalchemy as sa
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, timezone
from logging import getLogger
from .settings import settings
from .models import Session as DBSession
from .dependencies import engine

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from jsonschema import validate
import jsonschema
import json
from .kafka import SCHEMAS

logger = getLogger(__name__)

app = Celery('auth', broker=settings.celery_broker_url, backend=settings.celery_result_backend)

@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_wrapper(self, to: str, subject: str, body: str):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_email_async(to, subject, body))
    except Exception as exc:
        logger.error(f"Email task failed: {exc}")
        raise self.retry(exc=exc)

async def send_email_async(to: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = settings.smtp_user
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        await send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            use_tls=True,
        )
        logger.info(f"Email sent to {to}")
    except SMTPException as e:
        logger.error(f"SMTP error sending email to {to}: {e}")
        raise

@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_kafka_event_wrapper(self, topic: str, event_data: dict, schema_name: str):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_kafka_event_async(topic, event_data, schema_name))
    except Exception as exc:
        logger.error(f"Kafka task failed: {exc}")
        raise self.retry(exc=exc)

async def send_kafka_event_async(topic: str, event_data: dict, schema_name: str):
    schema = SCHEMAS.get(schema_name)
    if not schema:
        logger.error(f"Invalid schema name provided to Celery task: {schema_name}")
        raise ValueError(f"Invalid schema name: {schema_name}")

    try:
        validate(instance=event_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Invalid event data from Celery task: {e}")
        raise
    
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    try:
        await producer.start()
        await producer.send_and_wait(topic, value=json.dumps(event_data).encode('utf-8'))
        logger.info(f"Event sent via Celery to {topic}: {event_data.get('event')}")
    except KafkaConnectionError as e:
        logger.warning(f"Kafka connection failed in Celery task: {e}")
        raise
    except Exception as e:
        logger.error(f"Kafka send failed in Celery task: {e}")
        raise
    finally:
        await producer.stop()

@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def cleanup_sessions_wrapper(self):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(cleanup_sessions_async())
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
        raise self.retry(exc=exc)


async def cleanup_sessions_async():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as db:
        await db.execute(
            delete(DBSession).where(
                or_(
                    DBSession.expires_at < datetime.now(timezone.utc),
                    DBSession.revoked == sa.true()
                )
            )
        )
        await db.commit()
    logger.info("Expired/revoked sessions cleaned up")

app.conf.beat_schedule = {
    "cleanup-daily": {
        "task": "app.tasks.cleanup_sessions_wrapper",
        "schedule": crontab(hour=3, minute=0),
    },
}