from enum import Enum


class GoalStatus(str, Enum):
    """Статусы цели."""

    ONGOING = "ongoing"
    ACHIEVED = "achieved"
    EXPIRED = "expired"
    CLOSED = "closed"


class GoalEventType(str, Enum):
    """Типы событий целей."""

    CREATED = "goal.created"
    CHANGED = "goal.changed"
    UPDATED = "goal.updated"
    ACHIEVED = "goal.achieved"
    EXPIRED = "goal.expired"
    APPROACHING = "goal.approaching"
    ALERT = "goal.alert"


class TransactionType(str, Enum):
    """Типы транзакций."""

    INCOME = "income"
    EXPENSE = "expense"


class GoalPriority(str, Enum):
    """Приоритеты цели."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
