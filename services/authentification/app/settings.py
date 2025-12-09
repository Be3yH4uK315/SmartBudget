from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property
import os

ROOT_DIR = Path(__file__).resolve().parent.parent

env_file_name = os.getenv("ENV_FILE", ".env")
env_file_path = ROOT_DIR / env_file_name

class DBSettings(BaseSettings):
    db_url: str

class SMTPSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_from_email: str
    smtp_from_name: str

class JWTSettings(BaseSettings):
    jwt_private_key_path: Path
    jwt_public_key_path: Path
    jwt_algorithm: str
    
    @cached_property
    def jwt_private_key(self) -> str:
        return self.jwt_private_key_path.read_text()

    @cached_property
    def jwt_public_key(self) -> str:
        return self.jwt_public_key_path.read_text()

class AppSettings(BaseSettings):
    env: str
    kafka_bootstrap_servers: str
    kafka_group_id: str
    redis_url: str
    arq_queue_name: str
    geoip_db_path: str
    frontend_url: str
    prometheus_port: int
    log_level: str
    tz: str

class Settings(BaseSettings):
    db: DBSettings
    smtp: SMTPSettings
    jwt: JWTSettings
    app: AppSettings

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",

    )

settings = Settings()