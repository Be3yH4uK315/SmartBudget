import asyncio
from celery import Celery
from aiosmtplib import send, SMTPException
from email.message import EmailMessage
import sqlalchemy as sa
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, timezone
from logging import getLogger
from .settings import settings
from .models import Session as DBSession
from .db import engine

logger = getLogger(__name__)

app = Celery('auth', broker=settings.celery_broker_url, backend=settings.celery_result_backend)

@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_wrapper(to: str, subject: str, body: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_email_async(to, subject, body))

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
def cleanup_sessions_wrapper():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cleanup_sessions_async())

async def cleanup_sessions_async():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as db:
        await db.execute(delete(DBSession).where(or_(DBSession.expires_at < datetime.now(timezone.utc), DBSession.revoked == sa.true())))
        await db.commit()
    logger.info("Expired sessions cleaned up")

app.conf.beat_schedule = {
    'cleanup-daily': {
        'task': 'app.tasks.cleanup_sessions_wrapper',
        'schedule': {'hour': 3, 'minute': 0},
    },
}