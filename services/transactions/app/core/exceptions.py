class TransactionServiceError(Exception):
    """Базовая ошибка сервиса транзакций."""


class TransactionNotFoundError(TransactionServiceError):
    """Транзакция не найдена."""


class TransactionAccessDeniedError(TransactionServiceError):
    """Нет доступа к транзакции."""


class InvalidTransactionDataError(TransactionServiceError):
    """Некорректные данные транзакции."""
