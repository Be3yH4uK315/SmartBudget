from smartbudget_shared.events import (
    AuthEventType,
    AuthUserPayload,
    EventEnvelope,
)

AuthEvent = EventEnvelope[AuthUserPayload]

__all__ = [
    "AuthEvent",
    "AuthEventType",
    "AuthUserPayload",
]
