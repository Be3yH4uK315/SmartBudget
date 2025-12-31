class ClassificationServiceError(Exception):
    """Базовый класс для ошибок сервиса."""
    pass

class ClassificationResultNotFoundError(ClassificationServiceError):
    """Результат классификации не найден."""
    pass

class CategoryNotFoundError(ClassificationServiceError):
    """Категория не найдена."""
    pass

class InvalidKafkaMessageError(ClassificationServiceError):
    """Ошибка валидации данных из Kafka."""
    pass

class ModelLoadError(ClassificationServiceError):
    """Ошибка загрузки ML модели."""
    pass