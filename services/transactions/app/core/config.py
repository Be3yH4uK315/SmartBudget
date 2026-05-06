from pydantic_settings import BaseSettings, SettingsConfigDict

from smartbudget_shared.config import (
    DBSettings as SharedDBSettings,
    ArqSettings as SharedArqSettings,
    AppSettings as SharedAppSettings,
)


class DBSettings(SharedDBSettings):
    """Настройки базы данных, унаследованные от общей конфигурации."""

    pass


class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_GROUP_ID: str = "transactions-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_ENABLE_AUTO_COMMIT: bool = False
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_BATCH_SIZE: int = 100
    KAFKA_TOPIC_TRANSACTION_NEW: str = "transaction.new"
    KAFKA_TOPIC_TRANSACTION_IMPORTED: str = "transaction.imported"
    KAFKA_TOPIC_TRANSACTION_GOAL: str = "transaction.goal"
    KAFKA_TOPIC_TRANSACTION_NEED_CATEGORY: str = "transaction.need_category"
    KAFKA_TOPIC_TRANSACTION_CLASSIFIED: str = "transaction.classified"
    KAFKA_TOPIC_TRANSACTION_UPDATED: str = "transaction.updated"
    KAFKA_TOPIC_TRANSACTION_DELETED: str = "transaction.deleted"
    KAFKA_TOPIC_BUDGET_EVENTS: str = "budget.transactions.events"
    KAFKA_TOPIC_NOTIFICATION_EVENTS: str = "notification.events"

    @property
    def consumer_topics(self) -> tuple[str, str]:
        return (
            self.KAFKA_TOPIC_TRANSACTION_CLASSIFIED,
            self.KAFKA_TOPIC_TRANSACTION_UPDATED,
        )


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения, унаследованные от общей конфигурации."""

    GOAL_CATEGORY_ID: int = 24


class Settings(BaseSettings):
    DB: DBSettings
    KAFKA: KafkaSettings
    ARQ: ArqSettings
    APP: AppSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
