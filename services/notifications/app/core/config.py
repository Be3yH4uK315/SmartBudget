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
    KAFKA_AUTO_OFFSET_RESET: str
    KAFKA_ENABLE_AUTO_COMMIT: bool
    KAFKA_SECURITY_PROTOCOL: str
    KAFKA_BATCH_SIZE: int
    KAFKA_NOTIFICATION_GROUP_ID: str
    KAFKA_TOPIC_EVENTS: str
    KAFKA_TOPIC_AUTH: str
    KAFKA_TOPIC_DLQ: str

    @property
    def consumer_group_id(self) -> str:
        return self.KAFKA_GROUP_ID or self.KAFKA_NOTIFICATION_GROUP_ID

    @property
    def consumer_topics(self) -> tuple[str, str]:
        return (self.KAFKA_TOPIC_EVENTS, self.KAFKA_TOPIC_AUTH)


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class AppSettings(SharedAppSettings):
    """Настройки приложения, унаследованные от общей конфигурации."""

    FRONTEND_URL: str


class SmtpSettings(BaseSettings):
    SMTP_ENABLED: bool
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str


class PushSettings(BaseSettings):
    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: str
    VAPID_CLAIMS_SUB: str


class Settings(BaseSettings):
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
