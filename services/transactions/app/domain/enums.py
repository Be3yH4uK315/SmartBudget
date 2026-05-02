from enum import Enum, IntEnum


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(str, Enum):
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    PENDING = "pending"


class TransactionTypeDb(IntEnum):
    INCOME = 0
    EXPENSE = 1


class TransactionStatusDb(IntEnum):
    REJECTED = 0
    CONFIRMED = 1
    PENDING = 2


TYPE_TO_DB = {
    TransactionType.INCOME: TransactionTypeDb.INCOME,
    TransactionType.EXPENSE: TransactionTypeDb.EXPENSE,
}

DB_TO_TYPE = {
    TransactionTypeDb.INCOME: TransactionType.INCOME,
    TransactionTypeDb.EXPENSE: TransactionType.EXPENSE,
}

STATUS_TO_DB = {
    TransactionStatus.REJECTED: TransactionStatusDb.REJECTED,
    TransactionStatus.CONFIRMED: TransactionStatusDb.CONFIRMED,
    TransactionStatus.PENDING: TransactionStatusDb.PENDING,
}

DB_TO_STATUS = {
    TransactionStatusDb.REJECTED: TransactionStatus.REJECTED,
    TransactionStatusDb.CONFIRMED: TransactionStatus.CONFIRMED,
    TransactionStatusDb.PENDING: TransactionStatus.PENDING,
}


def type_to_db(value: TransactionType | str | int) -> int:
    if isinstance(value, int):
        return value
    tx_type = value if isinstance(value, TransactionType) else TransactionType(value)
    return int(TYPE_TO_DB[tx_type])


def type_from_db(value: int) -> TransactionType:
    return DB_TO_TYPE[TransactionTypeDb(value)]


def status_to_db(value: TransactionStatus | str | int) -> int:
    if isinstance(value, int):
        return value
    status = value if isinstance(value, TransactionStatus) else TransactionStatus(value)
    return int(STATUS_TO_DB[status])


def status_from_db(value: int) -> TransactionStatus:
    return DB_TO_STATUS[TransactionStatusDb(value)]
