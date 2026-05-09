from pydantic_settings import BaseSettings, SettingsConfigDict

from smartbudget_shared.config import (
    DBSettings as SharedDBSettings,
    ArqSettings as SharedArqSettings,
    AppSettings as SharedAppSettings,
)


class DBSettings(SharedDBSettings):
    """Настройки базы данных, унаследованные от общей конфигурации."""

    pass


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_ID: str
    KAFKA_TOPIC: str | None = None
    KAFKA_DLQ_TOPIC: str | None = None
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int
    TOPIC_NEED_CATEGORY: str
    TOPIC_CLASSIFIED: str
    TOPIC_CATEGORY_UPDATED: str
    TOPIC_CLASSIFICATION_EVENTS: str
    TOPIC_NOTIFICATION_EVENTS: str
    TOPIC_NEED_CATEGORY_DLQ: str

    @property
    def consumer_topic(self) -> str:
        return self.KAFKA_TOPIC or self.TOPIC_NEED_CATEGORY

    @property
    def dlq_topic(self) -> str:
        return self.KAFKA_DLQ_TOPIC or self.TOPIC_NEED_CATEGORY_DLQ


class MLSettings(BaseSettings):
    MODEL_PATH: str
    DATASET_PATH: str
    ML_CONFIDENCE_THRESHOLD_ACCEPT: float
    ML_CONFIDENCE_THRESHOLD_AUDIT: float


class AppSettings(SharedAppSettings):
    """Настройки приложения, унаследованные от общей конфигурации."""

    FRONTEND_URL: str
    PROMETHEUS_PORT: int
    RULES_RELOAD_INTERVAL_SECONDS: int


class Settings(BaseSettings):
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
