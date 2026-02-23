from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = Field("development", env="APP__ENV")
    LOG_LEVEL: str = Field("INFO", env="APP__LOG_LEVEL")
    FRONTEND_URL: str = Field("http://localhost:3000", env="APP__FRONTEND_URL")

    DB_URL: str = Field(..., env="DB__DB_URL")
    DB_POOL_SIZE: int = Field(20, env="DB__DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB__DB_MAX_OVERFLOW")

    KAFKA_BOOTSTRAP_SERVERS: str = Field(..., env="KAFKA__KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_GROUP_ID: str = Field("notification-group", env="KAFKA__KAFKA_GROUP_ID")
    KAFKA_TOPIC_EVENTS: str = Field("notification.events", env="KAFKA__KAFKA_TOPIC_EVENTS")
    KAFKA_TOPIC_AUTH: str = Field("auth.events", env="KAFKA__KAFKA_TOPIC_AUTH")
    KAFKA_TOPIC_DLQ: str = Field("notification.events.dlq", env="KAFKA__KAFKA_TOPIC_DLQ")

    REDIS_URL: str = Field(..., env="ARQ__REDIS_URL")
    ARQ_QUEUE_NAME: str = Field("notification_tasks", env="ARQ__ARQ_QUEUE_NAME")

    SMTP_HOST: str = Field("localhost", env="SMTP__HOST")
    SMTP_PORT: int = Field(1025, env="SMTP__PORT")
    SMTP_USER: str = Field("", env="SMTP__USER")
    SMTP_PASS: str = Field("", env="SMTP__PASS")
    SMTP_FROM_EMAIL: str = Field("noreply@smartbudget.com", env="SMTP__FROM_EMAIL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
