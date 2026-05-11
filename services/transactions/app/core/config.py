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
    """Настройки Kafka для transactions service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_TRANSACTION_EVENTS: str = KafkaTopic.TRANSACTION_EVENTS
    KAFKA_TOPIC_CLASSIFICATION_EVENTS: str = KafkaTopic.CLASSIFICATION_EVENTS

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str]:
        """Возвращает topics, которые читает transactions consumer."""
        return (self.KAFKA_TOPIC_CLASSIFICATION_EVENTS,)


class ArqSettings(SharedArqSettings):
    """Настройки ARQ."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения."""

    GOAL_CATEGORY_ID: int


class Settings(BaseSettings):
    """Корневая конфигурация transactions service."""

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
