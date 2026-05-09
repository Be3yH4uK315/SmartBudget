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
    """Настройки Kafka для transactions service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_TRANSACTION_NEW: str
    KAFKA_TOPIC_TRANSACTION_IMPORTED: str
    KAFKA_TOPIC_TRANSACTION_GOAL: str
    KAFKA_TOPIC_TRANSACTION_NEED_CATEGORY: str
    KAFKA_TOPIC_TRANSACTION_CLASSIFIED: str
    KAFKA_TOPIC_TRANSACTION_UPDATED: str
    KAFKA_TOPIC_TRANSACTION_CATEGORY_UPDATED: str
    KAFKA_TOPIC_TRANSACTION_DELETED: str
    KAFKA_TOPIC_BUDGET_EVENTS: str
    KAFKA_TOPIC_NOTIFICATION_EVENTS: str

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str, str]:
        """Возвращает topics, которые читает transactions consumer."""
        return (
            self.KAFKA_TOPIC_TRANSACTION_CLASSIFIED,
            self.KAFKA_TOPIC_TRANSACTION_CATEGORY_UPDATED,
        )


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
