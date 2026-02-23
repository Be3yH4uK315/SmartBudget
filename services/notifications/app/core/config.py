from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    DB_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_NOTIFICATION_GROUP_ID: str = "notification-group"
    KAFKA_TOPIC_EVENTS: str = "notification.events"
    KAFKA_TOPIC_AUTH: str = "auth.events"
    KAFKA_TOPIC_DLQ: str = "notification.events.dlq"

class ArqSettings(BaseSettings):
    REDIS_URL: str
    ARQ_QUEUE_NAME: str = "notification_tasks"

class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    TZ: str = "UTC"
    FRONTEND_URL: str

class SmtpSettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 1025
    USER: str = ""
    PASS: str = ""
    FROM_EMAIL: str = "noreply@smartbudget.com"

class Settings(BaseSettings):
    DB: DBSettings
    KAFKA: KafkaSettings
    ARQ: ArqSettings
    APP: AppSettings
    SMTP: SmtpSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

settings = Settings()
