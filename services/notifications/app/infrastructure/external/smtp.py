import logging
from email.message import EmailMessage
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, html_content: str) -> None:
    """Асинхронная отправка HTML-письма через SMTP."""
    message = EmailMessage()
    message["From"] = settings.SMTP.FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP.HOST,
            port=settings.SMTP.PORT,
            username=settings.SMTP.USER or None,
            password=settings.SMTP.PASS or None,
            use_tls=(settings.SMTP.PORT == 465),
            start_tls=(settings.SMTP.PORT == 587),
        )
        logger.info("Email sent successfully to %s", to_email)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        raise
