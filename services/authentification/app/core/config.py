from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property

class DBSettings(BaseSettings):
    DB_URL: str
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int

class SMTPSettings(BaseSettings):
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str

class JWTSettings(BaseSettings):
    JWT_PRIVATE_KEY_PATH: Path
    JWT_PUBLIC_KEY_PATH: Path
    JWT_ALGORITHM: str
    
    @cached_property
    def JWT_PRIVATE_KEY(self) -> str:
        return self.JWT_PRIVATE_KEY_PATH.read_text()

    @cached_property
    def JWT_PUBLIC_KEY(self) -> str:
        return self.JWT_PUBLIC_KEY_PATH.read_text()

class ArqSettings(BaseSettings):
    REDIS_URL: str
    ARQ_QUEUE_NAME: str

class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_AUTH_GROUP_ID: str
    KAFKA_AUTH_EVENTS_TOPIC: str

class GeoSettings(BaseSettings):
    DADATA_API_KEY: str
    DADATA_SECRET_KEY: str

class AppSettings(BaseSettings):
    ENV: str
    FRONTEND_URL: str
    PROMETHEUS_PORT: int
    LOG_LEVEL: str
    TZ: str
    DUMMY_HASH: str

class Settings(BaseSettings):
    DB: DBSettings
    SMTP: SMTPSettings
    JWT: JWTSettings
    ARQ: ArqSettings
    KAFKA: KafkaSettings
    GEO: GeoSettings
    APP: AppSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",

    )

settings = Settings()