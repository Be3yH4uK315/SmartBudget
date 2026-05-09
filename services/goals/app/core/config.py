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
        return self.KAFKA_GROUP_ID or self.KAFKA_GOALS_GROUP_ID

    @property
    def consumer_topic(self) -> str:
        return self.KAFKA_TOPIC or self.KAFKA_TOPIC_TRANSACTION_GOAL

    @property
    def consumer_topics(self) -> tuple[str, str]:
        return (self.consumer_topic, self.KAFKA_TOPIC_TRANSACTION_DELETED)

    @property
    def dlq_topic(self) -> str:
        return self.KAFKA_DLQ_TOPIC or self.KAFKA_TOPIC_TRANSACTION_DLQ


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения, унаследованные от общей конфигурации."""

    FRONTEND_URL: str


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
