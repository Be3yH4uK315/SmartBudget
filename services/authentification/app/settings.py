from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = 'dev'
    db_url: str
    kafka_bootstrap_servers: str
    kafka_group_id: str = "auth-group"
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_pass: str
    geoip_db_path: str
    jwt_secret: str
    prometheus_port: int = 8001
    log_level: str = "INFO"
    tz: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding="utf-8",
    )

settings = Settings()