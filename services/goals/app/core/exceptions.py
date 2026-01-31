class GoalServiceError(Exception):
    """Базовый класс для ошибок сервиса."""
    pass

class GoalNotFoundError(GoalServiceError):
    """Цель не найдена."""
    pass

class InvalidGoalDataError(GoalServiceError):
    """Некорректные данные для операции с целью."""
    pass