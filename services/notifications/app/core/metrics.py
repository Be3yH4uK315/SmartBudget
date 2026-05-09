from prometheus_client import Counter, Gauge

NOTIFICATIONS_CREATED_TOTAL = Counter(
    "notifications_created_total",
    "Total number of in-app notifications created",
    ["service", "notification_type"],
)

BACKGROUND_TASKS_ENQUEUED = Counter(
    "background_tasks_enqueued_total",
    "Total number of ARQ tasks scheduled",
    ["task_name"],
)

KAFKA_CONSUMER_LAG = Gauge(
    "kafka_consumer_lag",
    "Approximate lag of kafka consumer group",
    ["topic", "partition"],
)

KAFKA_DLQ_ERRORS = Counter(
    "kafka_dlq_errors_total",
    "Total number of messages sent to DLQ",
    ["topic", "reason"],
)
