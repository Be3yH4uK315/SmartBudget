from smartbudget_shared.events import (
    EventEnvelope,
    TransactionDeletedPayload,
    TransactionGoalAppliedPayload,
)

TransactionGoalAppliedEvent = EventEnvelope[TransactionGoalAppliedPayload]
TransactionDeletedEvent = EventEnvelope[TransactionDeletedPayload]

__all__ = [
    "TransactionGoalAppliedEvent",
    "TransactionDeletedEvent",
]
