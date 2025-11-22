from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property
import os

ROOT_DIR = Path(__file__).resolve().parent.parent

env_file_name = os.getenv("ENV_FILE", ".env")
env_file_path = ROOT_DIR / env_file_name

class Settings(BaseSettings):
    env: str = 'dev'
    db_url: str
    kafka_bootstrap_servers: str
    kafka_group_id: str = "auth-group"
    redis_url: str
    arq_queue_name: str = "auth_tasks"
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from_email: str = "no-reply@example.com"
    smtp_from_name: str = "SmartBudget"
    geoip_db_path: str
    frontend_url: str = "http://127.0.0.1:3000"
    jwt_private_key_path: Path = ROOT_DIR / "certs" / "jwt-private.pem"
    jwt_public_key_path: Path = ROOT_DIR / "certs" / "jwt-public.pem"
    jwt_algorithm: str = "RS256"
    
    @cached_property
    def jwt_private_key(self) -> str:
        return self.jwt_private_key_path.read_text()

    @cached_property
    def jwt_public_key(self) -> str:
        return self.jwt_public_key_path.read_text()
    
    prometheus_port: int = 8001
    log_level: str = "INFO"
    tz: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
    )

settings = Settings()