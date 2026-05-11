from enum import Enum


class NotificationType(str, Enum):
    """Типы уведомлений."""

    INFO = "info"
    SUCCESS = "success"
    ALERT = "alert"
    WARNING = "warning"
    SYSTEM = "system"


class NotificationServiceType(str, Enum):
    """Сервисы-источники уведомлений."""

    limitAmount = "limitAmount"
    BUDGET = "Budget"
    GOALS = "Goals"
    TRANSACTIONS = "Transactions"
    SECURITY = "Security"


class NotificationStatus(str, Enum):
    """Статусы уведомлений."""

    UNREAD = "unread"
    READ = "read"
