from dataclasses import dataclass
from typing import List

@dataclass
class EventRouteConfig:
    service: str
    type: str
    title_key: str
    message_key: str
    default_channels: List[str]

EVENT_REGISTRY = {
    # === Лимиты (Limit) ===
    "budget.limit.reached_80": EventRouteConfig(
        service="Limit", type="alert", 
        title_key="Limit.preOverflow.title", message_key="Limit.preOverflow.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "budget.limit.exceeded": EventRouteConfig(
        service="Limit", type="warning", 
        title_key="Limit.overflow.title", message_key="Limit.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),

    # === Общий бюджет (Budget) ===
    "budget.total.reached_80": EventRouteConfig(
        service="Budget", type="alert", 
        title_key="Budget.preOverflow.title", message_key="Budget.preOverflow.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "budget.total.exceeded": EventRouteConfig(
        service="Budget", type="warning", 
        title_key="Budget.overflow.title", message_key="Budget.overflow.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),
    "budget.settings.changed": EventRouteConfig(
        service="Budget", type="info", 
        title_key="Budget.settingsChanged.title", message_key="Budget.settingsChanged.message",
        default_channels=["IN_APP"]
    ),
    "budget.check.results": EventRouteConfig(
        service="Budget", type="info", 
        title_key="Budget.checkResults.title", message_key="Budget.checkResults.message",
        default_channels=["IN_APP"]
    ),

    # === Цели (Goals) ===
    "goal.created": EventRouteConfig(
        service="Goals", type="system", 
        title_key="Goals.goalCreated.title", message_key="Goals.goalCreated.message",
        default_channels=["IN_APP"]
    ),
    "goal.payment_missed": EventRouteConfig(
        service="Goals", type="alert", 
        title_key="Goals.missedPayment.title", message_key="Goals.missedPayment.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "goal.almost_achieved": EventRouteConfig(
        service="Goals", type="info", 
        title_key="Goals.almostAchieved.title", message_key="Goals.almostAchieved.message",
        default_channels=["IN_APP"]
    ),
    "goal.achieved": EventRouteConfig(
        service="Goals", type="success", 
        title_key="Goals.achieved.title", message_key="Goals.achieved.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    ),
    "goal.expired": EventRouteConfig(
        service="Goals", type="warning", 
        title_key="Goals.expired.title", message_key="Goals.expired.message",
        default_channels=["IN_APP", "PUSH"]
    ),
    "goal.deadline_approaching": EventRouteConfig(
        service="Goals", type="info", 
        title_key="Goals.deadlineIsComing.title", message_key="Goals.deadlineIsComing.message",
        default_channels=["IN_APP", "PUSH"]
    ),

    # === Транзакции (Transactions) ===
    "transaction.unclassified.found": EventRouteConfig(
        service="Transactions", type="info", 
        title_key="Transactions.unclassified.title", message_key="Transactions.unclassified.message",
        default_channels=["IN_APP"]
    ),
    "transaction.category.changed": EventRouteConfig(
        service="Transactions", type="info", 
        title_key="Transactions.categoryChanged.title", message_key="Transactions.categoryChanged.message",
        default_channels=["IN_APP"]
    ),

    # === Безопасность (Security) ===
    "auth.settings.changed": EventRouteConfig(
        service="Security", type="alert", 
        title_key="Security.settingsChanged.title", message_key="Security.settingsChanged.message",
        default_channels=["IN_APP", "EMAIL"]
    ),
    "auth.password.changed": EventRouteConfig(
        service="Security", type="info", 
        title_key="Security.passwordChanged.title", message_key="Security.passwordChanged.message",
        default_channels=["IN_APP", "EMAIL"]
    ),
    "auth.activity.suspicious": EventRouteConfig(
        service="Security", type="warning", 
        title_key="Security.suspiciousActivity.title", message_key="Security.suspiciousActivity.message",
        default_channels=["IN_APP", "PUSH", "EMAIL"]
    )
}
