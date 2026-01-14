from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property

from app.utils.crypto import hash_password

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
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    EMAIL_TOKEN_EXPIRE_SECONDS: int
    SESSION_CACHE_EXPIRE_DAYS: int
    JWT_AUDIENCE: str
    JWT_ISSUER: str
    
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

    @field_validator("DUMMY_HASH", mode="before")
    @classmethod
    def generate_dummy_hash(cls, v: str | None) -> str:
        if v:
            return v
        return hash_password("dummy_password_for_timing_protection")

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