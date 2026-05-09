from prometheus_client import Counter, Gauge


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
