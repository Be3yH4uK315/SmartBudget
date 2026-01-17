from enum import Enum

class GoalStatus(str, Enum):
    ONGOING = "ongoing"
    ACHIEVED = "achieved"
    EXPIRED = "expired"
    CLOSED = "closed"

class GoalEventType(str, Enum):
    CREATED = "goal.created"
    CHANGED = "goal.changed"
    UPDATED = "goal.updated"
    ACHIEVED = "goal.achieved"
    EXPIRED = "goal.expired"
    APPROACHING = "goal.approaching"
    ALERT = "goal.alert"

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"