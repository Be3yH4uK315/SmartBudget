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
    UPDATED = "goal.updated"
    DELETED = "goal.deleted"
    COMPLETED = "goal.completed"
    EXPIRED = "goal.expired"
    PROGRESS_CHANGED = "goal.progress_changed"
    THRESHOLD_REACHED = "goal.threshold_reached"


class TransactionType(str, Enum):
    """Типы транзакций."""

    INCOME = "income"
    EXPENSE = "expense"


class GoalPriority(str, Enum):
    """Приоритеты цели."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
