from dataclasses import dataclass
from typing import List, Sequence
from app.domain.enums import NotificationType, NotificationServiceType

@dataclass
class EventRouteConfig:
    service: NotificationServiceType
    type: NotificationType
    title_key: str
    message_key: str
    default_channels: List[str]
    props: Sequence[str] | None = None

EVENT_REGISTRY = {
    # === Лимиты (Limit) ===
    "budget.limit.reached_80": EventRouteConfig(
        service=NotificationServiceType.LIMIT, type=NotificationType.ALERT,
        title_key="Limit.preOverflow.title", message_key="Limit.preOverflow.message",
        default_channels=["IN_APP", "PUSH"],
        props=("categoryId",),
    ),
    "budget.limit.exceeded": EventRouteConfig(
        service=NotificationServiceType.LIMIT, type=NotificationType.WARNING,
        title_key="Limit.overflow.title", message_key="Limit.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=("categoryId",),
    ),

    # === Общий бюджет (Budget) ===
    "budget.total.reached_80": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.ALERT,
        title_key="Budget.preOverflow.title", message_key="Budget.preOverflow.message",
        default_channels=["IN_APP", "PUSH"],
        props=("value",),
    ),
    "budget.total.exceeded": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.WARNING,
        title_key="Budget.overflow.title", message_key="Budget.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),
    "budget.settings.changed": EventRouteConfig(
        service=NotificationServiceType.BUDGET, type=NotificationType.INFO,
        title_key="Budget.settingsChanged.title", message_key="Budget.settingsChanged.message",
        default_channels=["IN_APP"],
        props=("budgetId",),
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
        default_channels=["IN_APP"],
        props=("goalId", "name", "recommendedPayment"),
    ),
    "goal.payment_missed": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.ALERT,
        title_key="Goals.missedPayment.title", message_key="Goals.missedPayment.message",
        default_channels=["IN_APP", "PUSH"],
        props=("goalId", "name"),
    ),
    "goal.almost_achieved": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.INFO,
        title_key="Goals.almostAchieved.title", message_key="Goals.almostAchieved.message",
        default_channels=["IN_APP"],
        props=("goalId", "name"),
    ),
    "goal.achieved": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.SUCCESS,
        title_key="Goals.achieved.title", message_key="Goals.achieved.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=("goalId", "name"),
    ),
    "goal.expired": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.WARNING,
        title_key="Goals.expired.title", message_key="Goals.expired.message",
        default_channels=["IN_APP", "PUSH"],
        props=("goalId", "name"),
    ),
    "goal.deadline_approaching": EventRouteConfig(
        service=NotificationServiceType.GOALS, type=NotificationType.INFO,
        title_key="Goals.deadlineIsComing.title", message_key="Goals.deadlineIsComing.message",
        default_channels=["IN_APP", "PUSH"],
        props=("goalId", "name", "daysLeft", "currentPercent"),
    ),

    # === Транзакции (Transactions) ===
    "transaction.unclassified.found": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS, type=NotificationType.INFO,
        title_key="Transactions.unclassified.title", message_key="Transactions.unclassified.message",
        default_channels=["IN_APP"],
        props=("value",),
    ),
    "transaction.category.changed": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS, type=NotificationType.INFO,
        title_key="Transactions.categoryChanged.title", message_key="Transactions.categoryChanged.message",
        default_channels=["IN_APP"],
        props=("transactionId", "oldCategory", "newCategory"),
    ),

    # === Безопасность (Security) ===
    "auth.device.new_login": EventRouteConfig(
        service=NotificationServiceType.SECURITY, type=NotificationType.ALERT,
        title_key="Security.newLogin.title", message_key="Security.newLogin.message",
        default_channels=["IN_APP", "PUSH"]
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
