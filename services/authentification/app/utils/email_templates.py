import re
from html import escape
from urllib.parse import quote

from app.core.config import settings

TAG_RE = re.compile(r"<[^>]+>")


def to_plain_text(html: str) -> str:
    """Преобразует HTML-письмо в простой текст для fallback-части email."""
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n\n", text)
    text = TAG_RE.sub("", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _render_auth_email(
    *,
    subject: str,
    message_text: str,
    action_text: str,
    action_url: str,
    warning_text: str,
) -> str:
    """Рендерит auth email в едином стиле с notification service."""
    escaped_subject = escape(subject)
    escaped_message = escape(message_text)
    escaped_action_text = escape(action_text)
    escaped_action_url = escape(action_url, quote=True)
    escaped_warning = escape(warning_text)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 10px;">
        <h2 style="color: #333;">{escaped_subject}</h2>
        <p style="color: #555; line-height: 1.6;">{escaped_message}</p>
        <p style="margin: 24px 0;">
            <a href="{escaped_action_url}" style="display: inline-block; background-color: #111827; color: #fff; text-decoration: none; padding: 12px 18px; border-radius: 8px;">
                {escaped_action_text}
            </a>
        </p>
        <p style="color: #777; line-height: 1.6; font-size: 14px;">
            Если кнопка не работает, откройте ссылку:<br>
            <a href="{escaped_action_url}" style="color: #2563eb; word-break: break-all;">{escaped_action_url}</a>
        </p>
        <p style="color: #777; line-height: 1.6; font-size: 14px;">{escaped_warning}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            Вы получили это письмо, потому что действие было запрошено в приложении SmartBudget.
        </p>
    </div>
</body>
</html>"""


def get_verification_email_body(email: str, token: str) -> str:
    """Генерирует тело письма для верификации аккаунта."""
    encoded_email = quote(email)
    verify_url = f"{settings.APP.FRONTEND_URL}/auth/registration?token={token}&email={encoded_email}"

    return _render_auth_email(
        subject="Подтвердите email",
        message_text="Чтобы завершить регистрацию в SmartBudget, подтвердите адрес электронной почты.",
        action_text="Подтвердить email",
        action_url=verify_url,
        warning_text="Ссылка действительна в течение 15 минут. Если вы не регистрировались, просто проигнорируйте это письмо.",
    )


def get_password_reset_body(email: str, token: str) -> str:
    """Генерирует тело письма для сброса пароля."""
    encoded_email = quote(email)
    reset_url = f"{settings.APP.FRONTEND_URL}/auth/reset-password?token={token}&email={encoded_email}"

    return _render_auth_email(
        subject="Сброс пароля",
        message_text="Поступил запрос на сброс пароля для вашего аккаунта SmartBudget.",
        action_text="Установить новый пароль",
        action_url=reset_url,
        warning_text="Ссылка действительна в течение 15 минут. Если вы не запрашивали сброс, просто проигнорируйте это письмо.",
    )


def get_change_email_body(new_email: str, token: str) -> str:
    """Генерирует тело письма для подтверждения смены email."""
    confirm_url = (
        f"{settings.APP.FRONTEND_URL}/profile/change-email/confirm?token={token}"
    )

    return _render_auth_email(
        subject="Подтвердите смену email",
        message_text=f"Поступил запрос на смену email вашего аккаунта на {new_email}.",
        action_text="Подтвердить смену email",
        action_url=confirm_url,
        warning_text="Ссылка действительна в течение 15 минут. Если вы не инициировали это действие, срочно смените пароль.",
    )
