class BudgetServiceError(Exception):
    """Базовый класс для ошибок сервиса."""

    pass


class BudgetNotFoundError(BudgetServiceError):
    """Бюджет не найден."""

    pass


class BudgetAlreadyExistsError(BudgetServiceError):
    """Бюджет уже существует."""

    pass


class InvalidBudgetDataError(BudgetServiceError):
    """Некорректные данные для операции с бюджетом."""

    pass
