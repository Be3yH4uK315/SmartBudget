from dataclasses import dataclass
from typing import List
from app.domain.enums import NotificationType, NotificationServiceType

@dataclass
class EventRouteConfig:
    service: NotificationServiceType
    type: NotificationType
    title_key: str
    message_key: str
    default_channels: List[str]

EVENT_REGISTRY = {
    # === Лимиты (Limit) ===
    "budget.limit.reached_80": EventRouteConfig(
        service=NotificationServiceType.LIMIT, type=NotificationType.ALERT,
        title_key="Limit.preOverflow.title", message_key="Limit.preOverflow.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "budget.limit.exceeded": EventRouteConfig(
        service=NotificationServiceType.LIMIT, type=NotificationType.WARNING,
        title_key="Limit.overflow.title", message_key="Limit.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),

    # === Общий бюджет (Budget) ===
    "budget.total.reached_80": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.ALERT,
        title_key="Budget.preOverflow.title", message_key="Budget.preOverflow.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "budget.total.exceeded": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.WARNING,
        title_key="Budget.overflow.title", message_key="Budget.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),
    "budget.settings.changed": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.INFO,
        title_key="Budget.settingsChanged.title", message_key="Budget.settingsChanged.message",
        default_channels=["IN_APP"]
    ),
    "budget.check.results": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.INFO,
        title_key="Budget.checkResults.title", message_key="Budget.checkResults.message",
        default_channels=["IN_APP"]
    ),

    # === Цели (Goals) ===
    "goal.created": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.SYSTEM,
        title_key="Goals.goalCreated.title", message_key="Goals.goalCreated.message",
        default_channels=["IN_APP"]
    ),
    "goal.payment_missed": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.ALERT,
        title_key="Goals.missedPayment.title", message_key="Goals.missedPayment.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "goal.almost_achieved": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.INFO,
        title_key="Goals.almostAchieved.title", message_key="Goals.almostAchieved.message",
        default_channels=["IN_APP"]
    ),
    "goal.achieved": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.SUCCESS,
        title_key="Goals.achieved.title", message_key="Goals.achieved.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),
    "goal.expired": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.WARNING,
        title_key="Goals.expired.title", message_key="Goals.expired.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "goal.deadline_approaching": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.INFO,
        title_key="Goals.deadlineIsComing.title", message_key="Goals.deadlineIsComing.message",
        default_channels=["IN_APP", "PUSH"]
    ),

    # === Транзакции (Transactions) ===
    "transaction.unclassified.found": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS, type=NotificationType.INFO,
        title_key="Transactions.unclassified.title", message_key="Transactions.unclassified.message",
        default_channels=["IN_APP"]
    ),
    "transaction.category.changed": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS, type=NotificationType.INFO,
        title_key="Transactions.categoryChanged.title", message_key="Transactions.categoryChanged.message",
        default_channels=["IN_APP"]
    ),

    # === Безопасность (Security) ===
    "auth.device.new_login": EventRouteConfig(
        service=NotificationServiceType.SECURITY, type=NotificationType.ALERT,
        title_key="Security.settingsChanged.title", message_key="Security.settingsChanged.message",
        default_channels=["IN_APP", "EMAIL", "PUSH"]
    ),
    "auth.password.changed": EventRouteConfig(
        service=NotificationServiceType.SECURITY, type=NotificationType.INFO,
        title_key="Security.passwordChanged.title", message_key="Security.passwordChanged.message",
        default_channels=["IN_APP", "EMAIL"]
    ),
    "auth.activity.suspicious": EventRouteConfig(
        service=NotificationServiceType.SECURITY, type=NotificationType.WARNING,
        title_key="Security.suspiciousActivity.title", message_key="Security.suspiciousActivity.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    )
}