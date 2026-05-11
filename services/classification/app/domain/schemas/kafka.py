from smartbudget_shared.events import (
    EventEnvelope,
    TransactionNeedCategoryPayload,
)

TransactionNeedCategoryEvent = EventEnvelope[TransactionNeedCategoryPayload]

__all__ = [
    "TransactionNeedCategoryEvent",
]
