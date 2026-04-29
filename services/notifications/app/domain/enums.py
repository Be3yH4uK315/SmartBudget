from enum import Enum

class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    ALERT = "alert"
    WARNING = "warning"
    SYSTEM = "system"

class NotificationServiceType(str, Enum):
    LIMIT = "Limit"
    BUDGET = "Budget"
    GOALS = "Goals"
    TRANSACTIONS = "Transactions"
    SECURITY = "Security"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
