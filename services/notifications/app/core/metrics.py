from prometheus_client import Counter, Histogram, Gauge

NOTIFICATIONS_CREATED_TOTAL = Counter(
    "notifications_created_total",
    "Total number of in-app notifications created",
    ["service", "type"]
)

BACKGROUND_TASKS_ENQUEUED = Counter(
    "background_tasks_enqueued_total",
    "Total number of Arq tasks (push/email) scheduled",
    ["task_name"]
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
