from prometheus_client import Counter, Histogram, Gauge

GOALS_CREATED_TOTAL = Counter(
    "goals_created_total",
    "Total number of goals created",
)

GOAL_ACHIEVEMENT_TIME = Histogram(
    "goal_achievement_time_seconds",
    "Time taken to achieve a goal in seconds",
    buckets=[
        86_400,      # 1 день
        604_800,     # 1 неделя
        2_592_000,   # 1 месяц
        7_776_000,   # 3 месяца
        15_552_000,  # 6 месяцев
    ],
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