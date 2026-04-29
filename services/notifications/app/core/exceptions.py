class NotificationServiceError(Exception):
    """Базовый класс для ошибок сервиса уведомлений."""
    pass

class NotificationNotFoundError(NotificationServiceError):
    """Уведомление не найдено."""
    pass

class InvalidNotificationDataError(NotificationServiceError):
    """Некорректные данные для операции с уведомлением."""
    pass
