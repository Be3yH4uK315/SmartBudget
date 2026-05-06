from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedBaseSettings(BaseSettings):
    """Базовый класс для всех настроек, предоставляющий общую конфигурацию для всех сервисов."""

    model_config = SettingsConfigDict(extra="ignore")


class DBSettings(SharedBaseSettings):
    """Настройки базы данных."""

    DB_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10


class RedisSettings(SharedBaseSettings):
    """Настройки Redis."""

    REDIS_URL: str = "redis://redis_cache:6379/0"


class ArqSettings(SharedBaseSettings):
    """Настройки ARQ (async queue)."""

    REDIS_URL: str = "redis://redis_cache:6379/0"
    ARQ_QUEUE_NAME: str = "default_tasks"
    ARQ_TIMEZONE: str = "UTC"
    REDIS_MAX_CONNECTIONS: int = 50


class AppSettings(SharedBaseSettings):
    """Настройки базового приложения."""

    LOG_LEVEL: str = "INFO"
    TZ: str = "UTC"
    ENV: str = "development"


class KafkaSettings(SharedBaseSettings):
    """Настройки Kafka."""

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
