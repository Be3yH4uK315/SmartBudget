import logging
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from aiosmtplib import SMTP

from app.core.config import settings

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 60


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> None:
    """Отправляет HTML-письмо через SMTP."""
    message = _build_email_message(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
    )

    tls_context = ssl.create_default_context()
    use_implicit_tls = settings.SMTP.SMTP_PORT == 465

    client = SMTP(
        hostname=settings.SMTP.SMTP_HOST,
        port=settings.SMTP.SMTP_PORT,
        use_tls=use_implicit_tls,
        tls_context=tls_context,
        timeout=SMTP_TIMEOUT_SECONDS,
    )

    try:
        await client.connect()

        if not use_implicit_tls:
            await client.starttls(tls_context=tls_context)

        if settings.SMTP.SMTP_USER:
            await client.login(
                settings.SMTP.SMTP_USER,
                settings.SMTP.SMTP_PASS,
            )

        await client.send_message(message)
        logger.info("Email sent successfully to %s", to_email)

    except Exception as exc:
        logger.error(
            "Failed to send email to %s: %s",
            to_email,
            exc,
            exc_info=True,
        )
        raise

    finally:
        try:
            await client.quit()
        except Exception:
            logger.debug("SMTP client quit failed", exc_info=True)


def _build_email_message(
    to_email: str,
    subject: str,
    html_content: str,
) -> EmailMessage:
    """Формирует EmailMessage для SMTP-отправки."""
    message = EmailMessage()
    message["From"] = formataddr(
        (
            settings.SMTP.SMTP_FROM_NAME,
            settings.SMTP.SMTP_FROM_EMAIL,
        ),
    )
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    return message
