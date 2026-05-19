import logging
from typing import Any

from jinja2 import Environment, Template, TemplateError, TemplateNotFound

from app.infrastructure.external.smtp import send_email
from app.infrastructure.external.web_push import send_web_push_notifications

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "ru"
DEFAULT_NOTIFICATION_URL = "/notifications"
EMAIL_TEMPLATE_NAME = "base_email.html"
CATEGORY_NAMES_BY_LANGUAGE = {
    "ru": {
        1: "Прочее",
        2: "Продукты",
        3: "Кафе и рестораны",
        4: "Одежда и обувь",
        5: "Электроника",
        6: "Строительство и ремонт",
        7: "Товары для дома",
        8: "Красота и уход",
        9: "Зоотовары",
        10: "Книги и канцелярия",
        11: "Аптеки",
        12: "Медицинские услуги",
        13: "Топливо",
        14: "Автосервисы",
        15: "Автозапчасти",
        16: "Парковки и штрафы",
        17: "Онлайн подписки",
        18: "Игры",
        19: "Маркетплейсы",
        20: "Общественный транспорт",
        21: "Такси и каршеринг",
        22: "ЖКХ",
        23: "Связь и интернет",
        24: "Финансы",
        25: "Образование",
        26: "Развлечения",
        27: "Спорт",
        28: "Путешествия",
        29: "Благотворительность",
        30: "Цветы и подарки",
    },
    "en": {
        1: "Other",
        2: "Groceries",
        3: "Cafes & Restaurants",
        4: "Clothing & Shoes",
        5: "Electronics",
        6: "Construction & Renovation",
        7: "Home Goods",
        8: "Beauty & Personal Care",
        9: "Pet Supplies",
        10: "Books & Stationery",
        11: "Pharmacies",
        12: "Medical Services",
        13: "Fuel",
        14: "Car Services",
        15: "Auto Parts",
        16: "Parking & Fines",
        17: "Online Subscriptions",
        18: "Games",
        19: "Marketplaces",
        20: "Public Transport",
        21: "Taxi & Car Sharing",
        22: "Utilities",
        23: "Mobile & Internet",
        24: "Finance",
        25: "Education",
        26: "Entertainment",
        27: "Sports",
        28: "Travel",
        29: "Charity",
        30: "Flowers & Gifts",
    },
}


class SafeDict(dict):
    """Словарь, который оставляет {key}, если значения нет в props."""

    def __missing__(self, key: str) -> str:
        """Возвращает placeholder вместо KeyError."""
        return "{" + key + "}"


def get_push_url(message_key: str, props: dict[str, Any]) -> str:
    """Возвращает UI URL для клика по browser push."""
    if message_key.startswith("Goals.") and props.get("goal_id"):
        return f"/goals/{props['goal_id']}"

    if message_key.startswith(("Budget.", "Limit.")):
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


def _prepare_email_props(
    language: str,
    message_key: str,
    props: dict[str, Any],
) -> dict[str, Any]:
    """Подготавливает props для email без изменения in-app/push payload."""
    email_props = dict(props)
    if not message_key.startswith("Limit."):
        return email_props

    category_id = _to_int(email_props.get("category_id"))
    if category_id is None:
        return email_props

    category_name = _category_name(language, category_id)
    if category_name:
        email_props["category_id"] = category_name

    return email_props


def _category_name(language: str, category_id: int) -> str | None:
    """Возвращает локализованное название категории."""
    names = (
        CATEGORY_NAMES_BY_LANGUAGE.get(language)
        or CATEGORY_NAMES_BY_LANGUAGE[DEFAULT_LANGUAGE]
    )
    return names.get(category_id)


def _to_int(value: Any) -> int | None:
    """Безопасно приводит значение к int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
    email_props = _prepare_email_props(
        language=language,
        message_key=message_key,
        props=props or {},
    )
    safe_props = SafeDict(**email_props)

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
        props=email_props,
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
