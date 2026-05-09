from pydantic_settings import BaseSettings, SettingsConfigDict
from smartbudget_shared.config import (
    AppSettings as SharedAppSettings,
    ArqSettings as SharedArqSettings,
    DBSettings as SharedDBSettings,
)


class DBSettings(SharedDBSettings):
    """Настройки базы данных."""

    pass


class KafkaSettings(BaseSettings):
    """Настройки Kafka для goals service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str | None = None
    KAFKA_TOPIC: str | None = None
    KAFKA_DLQ_TOPIC: str | None = None

    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_GOALS_GROUP_ID: str
    KAFKA_TOPIC_TRANSACTION_GOAL: str
    KAFKA_TOPIC_TRANSACTION_DELETED: str
    KAFKA_TOPIC_BUDGET_EVENTS: str
    KAFKA_TOPIC_BUDGET_NOTIFICATION: str
    KAFKA_TOPIC_NOTIFICATION_EVENTS: str
    KAFKA_TOPIC_TRANSACTION_DLQ: str

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID or self.KAFKA_GOALS_GROUP_ID

    @property
    def consumer_topic(self) -> str:
        """Возвращает основной topic входящих событий транзакций."""
        return self.KAFKA_TOPIC or self.KAFKA_TOPIC_TRANSACTION_GOAL

    @property
    def consumer_topics(self) -> tuple[str, str]:
        """Возвращает topics, которые читает goals consumer."""
        return (
            self.consumer_topic,
            self.KAFKA_TOPIC_TRANSACTION_DELETED,
        )

    @property
    def dlq_topic(self) -> str:
        """Возвращает DLQ topic."""
        return self.KAFKA_DLQ_TOPIC or self.KAFKA_TOPIC_TRANSACTION_DLQ


class ArqSettings(SharedArqSettings):
    """Настройки ARQ."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения."""

    FRONTEND_URL: str


class Settings(BaseSettings):
    """Корневая конфигурация goals service."""

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
