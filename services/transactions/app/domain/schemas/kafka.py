from smartbudget_shared.events import (
    EventEnvelope,
    TransactionCategoryUpdatedPayload,
    TransactionClassifiedPayload,
)

TransactionClassifiedMessage = EventEnvelope[TransactionClassifiedPayload]
TransactionCategoryUpdatedMessage = EventEnvelope[TransactionCategoryUpdatedPayload]

__all__ = [
    "TransactionClassifiedMessage",
    "TransactionCategoryUpdatedMessage",
]