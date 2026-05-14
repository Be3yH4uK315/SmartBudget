import logging
from typing import Any

from jinja2 import Environment, Template, TemplateError, TemplateNotFound

from app.infrastructure.external.smtp import send_email
from app.infrastructure.external.web_push import send_web_push_notifications

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "ru"
DEFAULT_NOTIFICATION_URL = "/notifications"
EMAIL_TEMPLATE_NAME = "base_email.html"


class SafeDict(dict):
    """Словарь, который оставляет {key}, если значения нет в props."""

    def __missing__(self, key: str) -> str:
        """Возвращает placeholder вместо KeyError."""
        return "{" + key + "}"


def get_push_url(message_key: str, props: dict[str, Any]) -> str:
    """Возвращает UI URL для клика по browser push."""
    if message_key.startswith("Goals.") and props.get("goal_id"):
        return f"/goals/{props['goal_id']}"

    if message_key.startswith(("Budget.", "limitAmount.")):
        return "/budget"

    if message_key.startswith("Security."):
        return "/settings/security"

    if message_key == "Transactions.unclassified.message":
        return "/transactions/?categoriesIds=1"

    if (
        message_key == "Transactions.categoryChanged.message"
        and props.get("transaction_id")
    ):
        return f"/transactions/{props['transaction_id']}"

    return DEFAULT_NOTIFICATION_URL


def get_translation(ctx: dict[str, Any], language: str, key: str) -> str:
    """Возвращает перевод по ключу или сам ключ, если перевод не найден."""
    translations: dict[str, dict[str, str]] = ctx.get("translations", {})
    locale_dict = translations.get(language) or translations.get(DEFAULT_LANGUAGE, {})

    return locale_dict.get(key, key)


async def send_email_task(
    ctx: dict[str, Any],
    user_id: Any,
    email: str,
    language: str,
    title_key: str,
    message_key: str,
    props: dict[str, Any],
) -> None:
    """Фоновая задача отправки email-уведомления."""
    safe_props = SafeDict(**(props or {}))

    subject = _render_translation(
        ctx=ctx,
        language=language,
        key=title_key,
        safe_props=safe_props,
    )
    message_text = _render_translation(
        ctx=ctx,
        language=language,
        key=message_key,
        safe_props=safe_props,
    )

    html_content = await _render_email_template(
        ctx=ctx,
        language=language,
        subject=subject,
        message_text=message_text,
        props=props or {},
    )

    await send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
    )

    logger.info(
        "Email notification sent",
        extra={
            "user_id": str(user_id),
            "email": email,
            "language": language,
            "title_key": title_key,
            "message_key": message_key,
        },
    )


async def send_push_task(
    ctx: dict[str, Any],
    user_id: Any,
    push_subscriptions: list[dict[str, Any]],
    language: str,
    title_key: str,
    message_key: str,
    props: dict[str, Any],
) -> None:
    """Фоновая задача отправки browser push-уведомления."""
    safe_props = SafeDict(**(props or {}))

    title = _render_translation(
        ctx=ctx,
        language=language,
        key=title_key,
        safe_props=safe_props,
    )
    body = _render_translation(
        ctx=ctx,
        language=language,
        key=message_key,
        safe_props=safe_props,
    )
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

    logger.info(
        "Push notification sent",
        extra={
            "user_id": str(user_id),
            "subscriptions_count": len(push_subscriptions),
            "language": language,
            "title_key": title_key,
            "message_key": message_key,
        },
    )


def _render_translation(
    ctx: dict[str, Any],
    language: str,
    key: str,
    safe_props: SafeDict,
) -> str:
    """Подставляет props в строку перевода."""
    template = get_translation(ctx, language, key)
    return template.format_map(safe_props)


async def _render_email_template(
    ctx: dict[str, Any],
    language: str,
    subject: str,
    message_text: str,
    props: dict[str, Any],
) -> str:
    """Рендерит HTML-шаблон email."""
    jinja_env: Environment = ctx["jinja_env"]
    template = _get_email_template(jinja_env, language)

    return await template.render_async(
        subject=subject,
        message_text=message_text,
        **props,
    )


def _get_email_template(jinja_env: Environment, language: str) -> Template:
    """Возвращает локализованный email template или fallback template."""
    localized_template_name = f"base_email_{language}.html"

    try:
        return jinja_env.get_template(localized_template_name)

    except TemplateNotFound:
        return jinja_env.get_template(EMAIL_TEMPLATE_NAME)

    except TemplateError as exc:
        logger.error(
            "Failed to load email template %s: %s",
            localized_template_name,
            exc,
            exc_info=True,
        )
        raise
