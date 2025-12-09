class AuthServiceError(Exception):
    """Базовый класс для ошибок сервиса аутентификации."""
    pass

class InvalidCredentialsError(AuthServiceError):
    """Неверные учетные данные."""
    pass

class InvalidTokenError(AuthServiceError):
    """Невалидный или просроченный токен."""
    pass

class EmailAlreadyExistsError(AuthServiceError):
    """Email уже зарегистрирован."""
    pass
    
class UserNotFoundError(AuthServiceError):
    """Пользователь не найден."""
    pass

class UserInactiveError(AuthServiceError):
    """Пользователь неактивен."""
    pass

class TooManyAttemptsError(AuthServiceError):
    """Слишком много попыток."""
    pass