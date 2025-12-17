from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
env_file_name = os.getenv("ENV_FILE", ".env")
env_file_path = ROOT_DIR / env_file_name

class DBSettings(BaseSettings):
    db_url: str

class KafkaSettings(BaseSettings):
    kafka_bootstrap_servers: str
    kafka_group_id: str
    topic_need_category: str
    topic_classified: str
    topic_classification_events: str
    topic_updated: str
    topic_need_category_dlq: str

class RedisSettings(BaseSettings):
    redis_url: str

class ArqSettings(BaseSettings):
    arq_queue_name: str

class MLSettings(BaseSettings):
    model_path: str
    dataset_path: str
    ml_confidence_threshold_accept: float
    ml_confidence_threshold_audit: float

class AppSettings(BaseSettings):
    env: str
    frontend_url: str
    prometheus_port: int
    log_level: str
    tz: str

class Settings(BaseSettings):
    db: DBSettings
    kafka: KafkaSettings
    redis: RedisSettings
    arq: ArqSettings
    ml: MLSettings
    app: AppSettings

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        env_nested_delimiter="__"
    )

settings = Settings()