import logging
from typing import Any
from jinja2 import Environment

from app.infrastructure.external.smtp import send_email
from app.infrastructure.external.web_push import send_web_push_notifications

logger = logging.getLogger(__name__)

class SafeDict(dict):
    """Словарь, который оставляет `{ключ}` в строке, если ключа нет в props (защита от KeyError)."""
    def __missing__(self, key):
        return "{" + key + "}"


def get_push_url(message_key: str, props: dict) -> str:
    """Возвращает UI URL для клика по browser push."""
    if message_key.startswith("Goals.") and props.get("goal_id"):
        return f"/goals/{props['goal_id']}"
    if message_key.startswith("Budget.") or message_key.startswith("Limit."):
        return "/budget"
    if message_key.startswith("Security."):
        return "/settings/security"
    if message_key == "Transactions.unclassified.message":
        return "/transactions/?categoriesIds=30"
    return "/notifications"


def get_translation(ctx: dict, language: str, key: str) -> str:
    """Извлекает переведенную строку из словаря, загруженного в память при старте."""
    translations = ctx.get("translations", {})
    loc_dict = translations.get(language) or translations.get("ru", {})
    return loc_dict.get(key, key)

async def send_email_task(
    ctx: dict, user_id: Any, email: str, language: str,
    title_key: str, message_key: str, props: dict
) -> None:
    """Фоновая задача отправки транзакционного письма."""
    title_tpl = get_translation(ctx, language, title_key)
    message_tpl = get_translation(ctx, language, message_key)

    safe_props = SafeDict(**(props or {}))
    subject = title_tpl.format_map(safe_props)
    message_text = message_tpl.format_map(safe_props)

    jinja_env: Environment = ctx["jinja_env"]
    try:
        template = jinja_env.get_template(f"base_email_{language}.html")
    except Exception:
        template = jinja_env.get_template("base_email.html")
        
    html_content = await template.render_async(subject=subject, message_text=message_text, **(props or {}))

    await send_email(to_email=email, subject=subject, html_content=html_content)


async def send_push_task(
    ctx: dict, user_id: Any, push_subscriptions: list[dict], language: str,
    title_key: str, message_key: str, props: dict
) -> None:
    """Фоновая задача отправки PUSH-уведомления на устройства."""
    title_tpl = get_translation(ctx, language, title_key)
    message_tpl = get_translation(ctx, language, message_key)

    safe_props = SafeDict(**(props or {}))
    title = title_tpl.format_map(safe_props)
    body = message_tpl.format_map(safe_props)
    data = {
        **(props or {}),
        "url": get_push_url(message_key, props or {}),
    }

    await send_web_push_notifications(
        subscriptions=push_subscriptions,
        title=title,
        body=body,
        data=data,
    )
