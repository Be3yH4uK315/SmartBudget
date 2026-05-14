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
    # Общий бюджет
    "budget.total.threshold_reached": EventRouteConfig(
        service=NotificationServiceType.BUDGET,
        notification_type=NotificationType.WARNING,
        title_key="Budget.preOverflow.title",
        message_key="Budget.preOverflow.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "budget_id",
            "spent_amount",
            "limit_amount",
            "percent",
            "threshold_percent",
        ),
    ),
    "budget.total.exceeded": EventRouteConfig(
        service=NotificationServiceType.BUDGET,
        notification_type=NotificationType.ALERT,
        title_key="Budget.overflow.title",
        message_key="Budget.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=(
            "budget_id",
            "spent_amount",
            "limit_amount",
            "percent",
        ),
    ),

    # Лимиты категорий
    "budget.category.threshold_reached": EventRouteConfig(
        service=NotificationServiceType.CATEGORY_LIMITS,
        notification_type=NotificationType.WARNING,
        title_key="limit.preOverflow.title",
        message_key="limit.preOverflow.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "budget_id",
            "category_id",
            "spent_amount",
            "limit_amount",
            "percent",
            "threshold_percent",
        ),
    ),
    "budget.category.exceeded": EventRouteConfig(
        service=NotificationServiceType.CATEGORY_LIMITS,
        notification_type=NotificationType.ALERT,
        title_key="limit.overflow.title",
        message_key="limit.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=(
            "budget_id",
            "category_id",
            "spent_amount",
            "limit_amount",
            "percent",
        ),
    ),

    # Настройки и проверки бюджета
    "budget.settings.changed": EventRouteConfig(
        service=NotificationServiceType.BUDGET,
        notification_type=NotificationType.INFO,
        title_key="Budget.settingsChanged.title",
        message_key="Budget.settingsChanged.message",
        default_channels=["IN_APP"],
        props=("budget_id",),
    ),
    "budget.check.results": EventRouteConfig(
        service=NotificationServiceType.BUDGET,
        notification_type=NotificationType.INFO,
        title_key="Budget.checkResults.title",
        message_key="Budget.checkResults.message",
        default_channels=["IN_APP"],
        props=(
            "budget_id",
            "total_exceeded_count",
            "category_exceeded_count",
        ),
    ),

    # Цели
    "goal.created": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.SUCCESS,
        title_key="Goals.goalCreated.title",
        message_key="Goals.goalCreated.message",
        default_channels=["IN_APP"],
        props=(
            "goal_id",
            "name",
            "recommended_payment",
        ),
    ),
    "goal.completed": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.SUCCESS,
        title_key="Goals.achieved.title",
        message_key="Goals.achieved.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=(
            "goal_id",
            "name",
            "current_amount",
            "target_amount",
        ),
    ),
    "goal.expired": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.ALERT,
        title_key="Goals.expired.title",
        message_key="Goals.expired.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "goal_id",
            "name",
            "progress_percent",
        ),
    ),
    "goal.threshold_reached": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.INFO,
        title_key="Goals.thresholdReached.title",
        message_key="Goals.thresholdReached.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "goal_id",
            "name",
            "progress_percent",
            "threshold_percent",
        ),
    ),
    "goal.deadline_approaching": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.WARNING,
        title_key="Goals.deadlineIsComing.title",
        message_key="Goals.deadlineIsComing.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "goal_id",
            "name",
            "days_left",
            "current_percent",
        ),
    ),
    "goal.payment_missed": EventRouteConfig(
        service=NotificationServiceType.GOALS,
        notification_type=NotificationType.WARNING,
        title_key="Goals.missedPayment.title",
        message_key="Goals.missedPayment.message",
        default_channels=["IN_APP", "PUSH"],
        props=(
            "goal_id",
            "name",
        ),
    ),

    # Транзакции
    "transaction.unclassified.found": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS,
        notification_type=NotificationType.INFO,
        title_key="Transactions.unclassified.title",
        message_key="Transactions.unclassified.message",
        default_channels=["IN_APP"],
        props=(
            "amount",
            "count",
        ),
    ),
    "transaction.category.changed": EventRouteConfig(
        service=NotificationServiceType.TRANSACTIONS,
        notification_type=NotificationType.INFO,
        title_key="Transactions.categoryChanged.title",
        message_key="Transactions.categoryChanged.message",
        default_channels=["IN_APP"],
        props=(
            "transaction_id",
            "old_category_id",
            "new_category_id",
        ),
    ),

    # Безопасность
    "user.registered": EventRouteConfig(
        service=NotificationServiceType.SECURITY,
        notification_type=NotificationType.INFO,
        title_key="Security.registration.title",
        message_key="Security.registration.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=None,
    ),
    "auth.device.new_login": EventRouteConfig(
        service=NotificationServiceType.SECURITY,
        notification_type=NotificationType.SYSTEM,
        title_key="Security.newLogin.title",
        message_key="Security.newLogin.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=None,
    ),
    "user.password_changed": EventRouteConfig(
        service=NotificationServiceType.SECURITY,
        notification_type=NotificationType.SYSTEM,
        title_key="Security.passwordChanged.title",
        message_key="Security.passwordChanged.message",
        default_channels=["IN_APP", "EMAIL"],
        props=None,
    ),
    "auth.activity.suspicious": EventRouteConfig(
        service=NotificationServiceType.SECURITY,
        notification_type=NotificationType.ALERT,
        title_key="Security.suspiciousActivity.title",
        message_key="Security.suspiciousActivity.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"],
        props=None,
    ),
}
