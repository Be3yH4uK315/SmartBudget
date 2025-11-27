from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

ROOT_DIR = Path(__file__).resolve().parent.parent

env_file_name = os.getenv("ENV_FILE", ".env")
env_file_path = ROOT_DIR / env_file_name

class Settings(BaseSettings):
    """
    Настройки сервиса категоризации.
    """
    env: str = 'dev'
    db_url: str
    kafka_bootstrap_servers: str
    kafka_group_id: str
    redis_url: str
    topic_need_category: str
    topic_classified: str
    topic_classification_events: str
    topic_updated: str
    topic_need_category_dlq: str
    arq_queue_name: str
    model_path: str
    dataset_path: str
    ml_confidence_threshold_accept: float
    ml_confidence_threshold_audit: float
    frontend_url: str = "http://localhost:3000"
    prometheus_port: int = 8001
    log_level: str = "INFO"
    tz: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
    )

settings = Settings()