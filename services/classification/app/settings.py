from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    DB_URL: str
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int

class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_ID: str
    TOPIC_NEED_CATEGORY: str
    TOPIC_CLASSIFIED: str
    TOPIC_CLASSIFICATION_EVENTS: str
    TOPIC_UPDATED: str
    TOPIC_NEED_CATEGORY_DLQ: str

class ArqSettings(BaseSettings):
    ARQ_QUEUE_NAME: str
    REDIS_URL: str

class MLSettings(BaseSettings):
    MODEL_PATH: str
    DATASET_PATH: str
    ML_CONFIDENCE_THRESHOLD_ACCEPT: float
    ML_CONFIDENCE_THRESHOLD_AUDIT: float

class AppSettings(BaseSettings):
    ENV: str
    FRONTEND_URL: str
    PROMETHEUS_PORT: int
    LOG_LEVEL: str
    TZ: str

class Settings(BaseSettings):
    DB: DBSettings
    KAFKA: KafkaSettings
    ARQ: ArqSettings
    ML: MLSettings
    APP: AppSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )

settings = Settings()