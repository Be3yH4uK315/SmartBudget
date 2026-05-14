from pydantic import Field
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
    """Настройки Kafka для notification service."""

    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_GROUP_ID: str
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int

    KAFKA_TOPIC_AUTH_EVENTS: str = KafkaTopic.AUTH_EVENTS
    KAFKA_TOPIC_BUDGET_EVENTS: str = KafkaTopic.BUDGET_EVENTS
    KAFKA_TOPIC_GOAL_EVENTS: str = KafkaTopic.GOAL_EVENTS
    KAFKA_TOPIC_TRANSACTION_EVENTS: str = KafkaTopic.TRANSACTION_EVENTS
    KAFKA_TOPIC_DLQ: str = KafkaTopic.DLQ

    @property
    def consumer_group_id(self) -> str:
        """Возвращает group id consumer-а."""
        return self.KAFKA_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str, ...]:
        """Возвращает topics, которые читает notification consumer."""
        return (
            self.KAFKA_TOPIC_AUTH_EVENTS,
            self.KAFKA_TOPIC_BUDGET_EVENTS,
            self.KAFKA_TOPIC_GOAL_EVENTS,
            self.KAFKA_TOPIC_TRANSACTION_EVENTS,
        )

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


class SmtpSettings(BaseSettings):
    """Настройки SMTP."""

    SMTP_ENABLED: bool
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str


class PushSettings(BaseSettings):
    """Настройки Web Push."""

    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: str
    VAPID_CLAIMS_SUB: str


class Settings(BaseSettings):
    """Корневая конфигурация notification service."""

    DB: DBSettings
    KAFKA: KafkaSettings
    ARQ: ArqSettings
    APP: AppSettings
    SMTP: SmtpSettings
    PUSH: PushSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
