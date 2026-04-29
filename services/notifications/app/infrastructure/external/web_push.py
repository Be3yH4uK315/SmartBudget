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
    """Send browser Web Push notifications to stored Push API subscriptions."""
    if not subscriptions:
        return

    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "url": (data or {}).get("url", "/"),
            "data": data or {},
        }
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
            )

    logger.info(
        "Web Push: sent %d notifications, failed %d",
        len(subscriptions) - failures,
        failures,
    )

def _send_web_push(subscription: dict[str, Any], payload: str) -> None:
    from pywebpush import webpush

    webpush(
        subscription_info=subscription,
        data=payload,
        vapid_private_key=settings.PUSH.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.PUSH.VAPID_CLAIMS_SUB},
    )
