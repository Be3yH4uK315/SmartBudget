import logging
from typing import Any
from jinja2 import Environment

from app.infrastructure.external.smtp import send_email
from app.infrastructure.external.fcm import send_push_notifications

logger = logging.getLogger(__name__)

class SafeDict(dict):
    """Словарь, который оставляет `{ключ}` в строке, если ключа нет в props (защита от KeyError)."""
    def __missing__(self, key):
        return "{" + key + "}"

def get_translation(ctx: dict, locale: str, key: str) -> str:
    """Извлекает переведенную строку из словаря, загруженного в память при старте."""
    translations = ctx.get("translations", {})
    loc_dict = translations.get(locale) or translations.get("ru", {})
    return loc_dict.get(key, key)

async def send_email_task(
    ctx: dict, user_id: Any, email: str, locale: str,
    title_key: str, message_key: str, props: dict
) -> None:
    """Фоновая задача отправки транзакционного письма."""
    title_tpl = get_translation(ctx, locale, title_key)
    message_tpl = get_translation(ctx, locale, message_key)

    safe_props = SafeDict(**(props or {}))
    subject = title_tpl.format_map(safe_props)
    message_text = message_tpl.format_map(safe_props)

    jinja_env: Environment = ctx["jinja_env"]
    try:
        template = jinja_env.get_template(f"base_email_{locale}.html")
    except Exception:
        template = jinja_env.get_template("base_email.html")
        
    html_content = await template.render_async(subject=subject, message_text=message_text, **(props or {}))

    await send_email(to_email=email, subject=subject, html_content=html_content)


async def send_push_task(
    ctx: dict, user_id: Any, fcm_tokens: list[str], locale: str,
    title_key: str, message_key: str, props: dict
) -> None:
    """Фоновая задача отправки PUSH-уведомления на устройства."""
    title_tpl = get_translation(ctx, locale, title_key)
    message_tpl = get_translation(ctx, locale, message_key)

    safe_props = SafeDict(**(props or {}))
    title = title_tpl.format_map(safe_props)
    body = message_tpl.format_map(safe_props)

    await send_push_notifications(
        tokens=fcm_tokens,
        title=title,
        body=body,
        data=props
    )
