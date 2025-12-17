from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    DB_URL: str

class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GOALS_GROUP_ID: str
    KAFKA_TOPIC_TRANSACTION_GOAL: str
    KAFKA_TOPIC_BUDGET_EVENTS: str
    KAFKA_TOPIC_BUDGET_NOTIFICATION: str

class ArqSettings(BaseSettings):
    REDIS_URL: str
    ARQ_QUEUE_NAME: str

class AppSettings(BaseSettings):
    LOG_LEVEL: str
    TZ: str
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
    )

settings = Settings()