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


class ArqSettings(SharedArqSettings):
    """Настройки ARQ."""

    pass


class KafkaSettings(BaseSettings):
    """Настройки Kafka для classification service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_TRANSACTION_EVENTS: str = KafkaTopic.TRANSACTION_EVENTS
    KAFKA_TOPIC_CLASSIFICATION_EVENTS: str = KafkaTopic.CLASSIFICATION_EVENTS
    KAFKA_TOPIC_DLQ: str = KafkaTopic.DLQ

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topic(self) -> str:
        """Возвращает topic, который читает classification consumer."""
        return self.KAFKA_TOPIC_TRANSACTION_EVENTS

    @property
    def dlq_topic(self) -> str:
        """Возвращает DLQ topic."""
        return self.KAFKA_TOPIC_DLQ


class MLSettings(BaseSettings):
    """Настройки ML pipeline."""

    MODEL_PATH: str
    DATASET_PATH: str
    ML_CONFIDENCE_THRESHOLD_ACCEPT: float
    ML_CONFIDENCE_THRESHOLD_AUDIT: float


class AppSettings(SharedAppSettings):
    """Настройки приложения."""

    FRONTEND_URL: str
    PROMETHEUS_PORT: int
    RULES_RELOAD_INTERVAL_SECONDS: int


class Settings(BaseSettings):
    """Корневая конфигурация classification service."""

    DB: DBSettings
    ARQ: ArqSettings
    KAFKA: KafkaSettings
    ML: MLSettings
    APP: AppSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
