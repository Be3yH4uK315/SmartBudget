from enum import Enum


class GoalStatus(str, Enum):
    """Статусы цели."""

    ONGOING = "ongoing"
    ACHIEVED = "achieved"
    EXPIRED = "expired"
    CLOSED = "closed"


class GoalEventType(str, Enum):
    """Типы событий goal service."""

    GOAL_CREATED = "goal.created"
    GOAL_CHANGED = "goal.changed"
    GOAL_UPDATED = "goal.updated"
    GOAL_DELETED = "goal.deleted"
    GOAL_ACHIEVED = "goal.achieved"
    GOAL_EXPIRED = "goal.expired"
    GOAL_APPROACHING = "goal.approaching"
    GOAL_ALERT = "goal.alert"
    GOAL_COMPLETED = "goal.completed"
    GOAL_PROGRESS_CHANGED = "goal.progress_changed"
    GOAL_TRANSACTION_CREATED = "goal.transaction.created"
    GOAL_TRANSACTION_DELETED = "goal.transaction.deleted"


class TransactionType(str, Enum):
    """Типы транзакций."""

    INCOME = "income"
    EXPENSE = "expense"


class GoalPriority(str, Enum):
    """Приоритеты цели."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
