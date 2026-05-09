class TransactionServiceError(Exception):
    """Базовая ошибка сервиса транзакций."""

    pass


class TransactionNotFoundError(TransactionServiceError):
    """Транзакция не найдена."""

    pass


class TransactionAccessDeniedError(TransactionServiceError):
    """Нет доступа к транзакции."""

    pass


class InvalidTransactionDataError(TransactionServiceError):
    """Некорректные данные транзакции."""

    pass
