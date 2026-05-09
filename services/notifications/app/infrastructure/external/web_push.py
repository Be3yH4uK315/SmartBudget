import asyncio
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_web_push_notifications(
    subscriptions: list[dict[str, Any]],
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Отправляет browser Web Push уведомления по сохраненным подпискам."""
    if not subscriptions:
        return

    payload = _build_web_push_payload(
        title=title,
        body=body,
        data=data,
    )

    failures = 0

    for subscription in subscriptions:
        try:
            await asyncio.to_thread(
                _send_web_push,
                subscription,
                payload,
            )
        except Exception as exc:
            failures += 1
            logger.warning(
                "Web Push send failed for endpoint %s: %s",
                subscription.get("endpoint"),
                exc,
                exc_info=True,
            )

    logger.info(
        "Web Push send completed. Success: %s, failed: %s",
        len(subscriptions) - failures,
        failures,
    )


def _build_web_push_payload(
    title: str,
    body: str,
    data: dict[str, Any] | None,
) -> str:
    """Формирует JSON payload для browser Web Push."""
    payload_data = data or {}

    return json.dumps(
        {
            "title": title,
            "body": body,
            "url": payload_data.get("url", "/"),
            "data": payload_data,
        },
        ensure_ascii=False,
    )


def _send_web_push(subscription: dict[str, Any], payload: str) -> None:
    """Синхронно отправляет одно Web Push уведомление."""
    from pywebpush import webpush

    webpush(
        subscription_info=subscription,
        data=payload,
        vapid_private_key=settings.PUSH.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.PUSH.VAPID_CLAIMS_SUB},
    )
