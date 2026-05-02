from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/transactions"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10


class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_GROUP_ID: str = "transactions-service"
    KAFKA_TOPIC_TRANSACTION_NEW: str = "transaction.new"
    KAFKA_TOPIC_TRANSACTION_IMPORTED: str = "transaction.imported"
    KAFKA_TOPIC_TRANSACTION_GOAL: str = "transaction.goal"
    KAFKA_TOPIC_TRANSACTION_NEED_CATEGORY: str = "transaction.need_category"
    KAFKA_TOPIC_TRANSACTION_CLASSIFIED: str = "transaction.classified"
    KAFKA_TOPIC_TRANSACTION_UPDATED: str = "transaction.updated"
    KAFKA_TOPIC_TRANSACTION_DELETED: str = "transaction.deleted"
    KAFKA_TOPIC_BUDGET_EVENTS: str = "budget.transactions.events"
    KAFKA_TOPIC_NOTIFICATION_EVENTS: str = "notification.events"


class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    TZ: str = "UTC"
    GOAL_CATEGORY_ID: int = 24


class Settings(BaseSettings):
    DB: DBSettings = DBSettings()
    KAFKA: KafkaSettings = KafkaSettings()
    APP: AppSettings = AppSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
