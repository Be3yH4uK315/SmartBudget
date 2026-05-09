from enum import Enum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(str, Enum):
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    PENDING = "pending"
