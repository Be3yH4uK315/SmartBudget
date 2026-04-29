import logging
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from aiosmtplib import SMTP

from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, html_content: str) -> None:
    """Асинхронная отправка HTML-письма через SMTP."""
    message = EmailMessage()
    message["From"] = formataddr(
        (settings.SMTP.SMTP_FROM_NAME, settings.SMTP.SMTP_FROM_EMAIL)
    )
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    tls_context = ssl.create_default_context()
    use_implicit_tls = settings.SMTP.SMTP_PORT == 465

    client = SMTP(
        hostname=settings.SMTP.SMTP_HOST,
        port=settings.SMTP.SMTP_PORT,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=60,
    )

    try:
        await client.connect()
        if not use_implicit_tls:
            await client.starttls(tls_context=tls_context)
        if settings.SMTP.SMTP_USER:
            await client.login(settings.SMTP.SMTP_USER, settings.SMTP.SMTP_PASS)
        await client.send_message(message)
        logger.info("Email sent successfully to %s", to_email)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        raise
    finally:
        try:
            await client.quit()
        except Exception:
            pass
