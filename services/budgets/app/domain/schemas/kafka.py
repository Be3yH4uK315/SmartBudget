from smartbudget_shared.events import (
    EventEnvelope,
    TransactionCategoryUpdatedPayload,
    TransactionClassifiedPayload,
    TransactionDeletedPayload,
    TransactionPayload,
    TransactionUpdatedPayload,
)

TransactionCreatedMessage = EventEnvelope[TransactionPayload]
TransactionUpdatedMessage = EventEnvelope[TransactionUpdatedPayload]
TransactionDeletedMessage = EventEnvelope[TransactionDeletedPayload]
TransactionClassifiedMessage = EventEnvelope[TransactionClassifiedPayload]
TransactionCategoryUpdatedMessage = EventEnvelope[TransactionCategoryUpdatedPayload]

__all__ = [
    "TransactionCreatedMessage",
    "TransactionUpdatedMessage",
    "TransactionDeletedMessage",
    "TransactionClassifiedMessage",
    "TransactionCategoryUpdatedMessage",
]
