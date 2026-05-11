from pydantic_settings import BaseSettings, SettingsConfigDict
from smartbudget_shared.config import (
    AppSettings as SharedAppSettings,
    ArqSettings as SharedArqSettings,
    DBSettings as SharedDBSettings,
)
from smartbudget_shared.events import KafkaTopic


class DBSettings(SharedDBSettings):
    """Настройки базы данных."""

    pass


class KafkaSettings(BaseSettings):
    """Настройки Kafka для goals service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_TRANSACTION_EVENTS: str = KafkaTopic.TRANSACTION_EVENTS
    KAFKA_TOPIC_GOAL_EVENTS: str = KafkaTopic.GOAL_EVENTS
    KAFKA_TOPIC_DLQ: str = KafkaTopic.DLQ

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str]:
        """Возвращает topics, которые читает goals consumer."""
        return (self.KAFKA_TOPIC_TRANSACTION_EVENTS,)

    @property
    def dlq_topic(self) -> str:
        """Возвращает DLQ topic."""
        return self.KAFKA_TOPIC_DLQ


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
