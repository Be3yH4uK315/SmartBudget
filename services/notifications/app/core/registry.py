# from dataclasses import dataclass
# from collections.abc import Sequence

# from app.domain.enums import NotificationServiceType, NotificationType


# @dataclass(frozen=True)
# class EventRouteConfig:
#     """Конфигурация маршрутизации входящего события в уведомление."""

#     service: NotificationServiceType
#     notification_type: NotificationType
#     title_key: str
#     message_key: str
#     default_channels: list[str]
#     props: Sequence[str] | None = None


# EVENT_REGISTRY: dict[str, EventRouteConfig] = {
#     # Лимиты
#     "budget.limitAmount.reached_80": EventRouteConfig(
#         service=NotificationServiceType.limitAmount,
#         notification_type=NotificationType.ALERT,
#         title_key="limitAmount.preOverflow.title",
#         message_key="limitAmount.preOverflow.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("category_id",),
#     ),
#     "budget.limitAmount.exceeded": EventRouteConfig(
#         service=NotificationServiceType.limitAmount,
#         notification_type=NotificationType.WARNING,
#         title_key="limitAmount.overflow.title",
#         message_key="limitAmount.overflow.message",
#         default_channels=["IN_APP", "PUSH", "EMAIL"],
#         props=("category_id",),
#     ),

#     # Общий бюджет
#     "budget.total.reached_80": EventRouteConfig(
#         service=NotificationServiceType.BUDGET,
#         notification_type=NotificationType.ALERT,
#         title_key="Budget.preOverflow.title",
#         message_key="Budget.preOverflow.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("percent",),
#     ),
#     "budget.total.exceeded": EventRouteConfig(
#         service=NotificationServiceType.BUDGET,
#         notification_type=NotificationType.WARNING,
#         title_key="Budget.overflow.title",
#         message_key="Budget.overflow.message",
#         default_channels=["IN_APP", "PUSH", "EMAIL"],
#     ),
#     "budget.settings.changed": EventRouteConfig(
#         service=NotificationServiceType.BUDGET,
#         notification_type=NotificationType.INFO,
#         title_key="Budget.settingsChanged.title",
#         message_key="Budget.settingsChanged.message",
#         default_channels=["IN_APP"],
#         props=("budget_id",),
#     ),
#     "budget.check.results": EventRouteConfig(
#         service=NotificationServiceType.BUDGET,
#         notification_type=NotificationType.INFO,
#         title_key="Budget.checkResults.title",
#         message_key="Budget.checkResults.message",
#         default_channels=["IN_APP"],
#     ),

#     # Цели
#     "goal.created": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.SYSTEM,
#         title_key="Goals.goalCreated.title",
#         message_key="Goals.goalCreated.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("goal_id", "name", "recommended_payment"),
#     ),
#     "goal.payment_missed": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.ALERT,
#         title_key="Goals.missedPayment.title",
#         message_key="Goals.missedPayment.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("goal_id", "name"),
#     ),
#     "goal.almost_achieved": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.INFO,
#         title_key="Goals.almostAchieved.title",
#         message_key="Goals.almostAchieved.message",
#         default_channels=["IN_APP"],
#         props=("goal_id", "name"),
#     ),
#     "goal.achieved": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.SUCCESS,
#         title_key="Goals.achieved.title",
#         message_key="Goals.achieved.message",
#         default_channels=["IN_APP", "PUSH", "EMAIL"],
#         props=("goal_id", "name"),
#     ),
#     "goal.expired": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.WARNING,
#         title_key="Goals.expired.title",
#         message_key="Goals.expired.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("goal_id", "name"),
#     ),
#     "goal.deadline_approaching": EventRouteConfig(
#         service=NotificationServiceType.GOALS,
#         notification_type=NotificationType.INFO,
#         title_key="Goals.deadlineIsComing.title",
#         message_key="Goals.deadlineIsComing.message",
#         default_channels=["IN_APP", "PUSH"],
#         props=("goal_id", "name", "days_left", "current_percent"),
#     ),

#     # Транзакции
#     "transaction.unclassified.found": EventRouteConfig(
#         service=NotificationServiceType.TRANSACTIONS,
#         notification_type=NotificationType.INFO,
#         title_key="Transactions.unclassified.title",
#         message_key="Transactions.unclassified.message",
#         default_channels=["IN_APP"],
#         props=("amount",),
#     ),
#     "transaction.category.changed": EventRouteConfig(
#         service=NotificationServiceType.TRANSACTIONS,
#         notification_type=NotificationType.INFO,
#         title_key="Transactions.categoryChanged.title",
#         message_key="Transactions.categoryChanged.message",
#         default_channels=["IN_APP"],
#         props=("transaction_id", "old_category_id", "new_category_id"),
#     ),

#     # Безопасность
#     "auth.device.new_login": EventRouteConfig(
#         service=NotificationServiceType.SECURITY,
#         notification_type=NotificationType.ALERT,
#         title_key="Security.newLogin.title",
#         message_key="Security.newLogin.message",
#         default_channels=["IN_APP", "PUSH"],
#     ),
#     "auth.password.changed": EventRouteConfig(
#         service=NotificationServiceType.SECURITY,
#         notification_type=NotificationType.INFO,
#         title_key="Security.passwordChanged.title",
#         message_key="Security.passwordChanged.message",
#         default_channels=["IN_APP", "EMAIL"],
#     ),
#     "auth.activity.suspicious": EventRouteConfig(
#         service=NotificationServiceType.SECURITY,
#         notification_type=NotificationType.WARNING,
#         title_key="Security.suspiciousActivity.title",
#         message_key="Security.suspiciousActivity.message",
#         default_channels=["IN_APP", "PUSH", "EMAIL"],
#     ),
# }

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.enums import NotificationServiceType, NotificationType


@dataclass(frozen=True)
class EventRouteConfig:
    """Конфигурация маршрутизации входящего события в уведомление."""

    service: NotificationServiceType
    notification_type: NotificationType
    title_key: str
    message_key: str
    default_channels: list[str]
    props: Sequence[str] | None = None


EVENT_REGISTRY: dict[str, EventRouteConfig] = {
    # Бюджеты
    "budget.threshold_reached": EventRouteConfig(
        service=NotificationServiceType.BUDGET,
        notification_type=NotificationType.ALERT,
        title_key="Budget.thresholdReached.title",
        message_key="Budget.thresholdReached.message",
        default_channels=["IN_APP", "PUSH"],
        props=("threshold_percent",),
    ),
    # Цели
    "goal.completed": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.SUCCESS,
        title_key="Goals.achieved.title",
        message_key="Goals.achieved.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=("goal_id",),
    ),
    "goal.expired": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.WARNING,
        title_key="Goals.expired.title",
        message_key="Goals.expired.message",
        default_channels=["IN_APP", "PUSH"],
        props=("goal_id",),
    ),
    "goal.threshold_reached": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.INFO,
        title_key="Goals.thresholdReached.title",
        message_key="Goals.thresholdReached.message",
        default_channels=["IN_APP", "PUSH"],
        props=("goal_id", "progress_percent", "threshold_percent"),
    ),
    # Безопасность
    "auth.password.changed": EventRouteConfig(
        service=NotificationServiceType.SECURITY,
        notification_type=NotificationType.INFO,
        title_key="Security.passwordChanged.title",
        message_key="Security.passwordChanged.message",
        default_channels=["IN_APP", "EMAIL"],
    ),
}
