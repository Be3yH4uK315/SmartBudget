from enum import Enum


class TransactionType(str, Enum):
    """Типы транзакций."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(str, Enum):
    """Статусы транзакций."""

    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    PENDING = "pending"
