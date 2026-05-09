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
    """Настройки Kafka для budgets service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_TRANSACTION_NEW: str
    KAFKA_TOPIC_TRANSACTION_UPDATED: str
    KAFKA_TOPIC_TRANSACTION_DELETED: str
    KAFKA_TOPIC_BUDGET_EVENTS: str
    KAFKA_TOPIC_NOTIFICATION_EVENTS: str
    KAFKA_TOPIC_BUDGET_DLQ: str

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str, str, str]:
        """Возвращает topics, которые читает budgets consumer."""
        return (
            self.KAFKA_TOPIC_TRANSACTION_NEW,
            self.KAFKA_TOPIC_TRANSACTION_UPDATED,
            self.KAFKA_TOPIC_TRANSACTION_DELETED,
        )

    @property
    def dlq_topic(self) -> str:
        """Возвращает DLQ topic."""
        return self.KAFKA_TOPIC_BUDGET_DLQ


class ArqSettings(SharedArqSettings):
    """Настройки ARQ."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения."""

    pass


class Settings(BaseSettings):
    """Корневая конфигурация budgets service."""

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
