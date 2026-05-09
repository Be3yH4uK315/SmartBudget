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
    def consumer_topics(self) -> tuple[str, str]:
        return (
            self.KAFKA_TOPIC_TRANSACTION_CLASSIFIED,
            self.KAFKA_TOPIC_TRANSACTION_CATEGORY_UPDATED,
        )


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения, унаследованные от общей конфигурации."""

    GOAL_CATEGORY_ID: int


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
