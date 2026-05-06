from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cached_property

from smartbudget_shared.config import (
    DBSettings as SharedDBSettings,
    ArqSettings as SharedArqSettings,
    AppSettings as SharedAppSettings,
)
from app.utils.crypto import hash_password_sync


class DBSettings(SharedDBSettings):
    """Настройки базы данных, унаследованные от общей конфигурации."""

    pass


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


class ArqSettings(SharedArqSettings):
    """Настройки ARQ, унаследованные от общей конфигурации."""

    pass


class KafkaSettings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_AUTH_GROUP_ID: str
    KAFKA_AUTH_EVENTS_TOPIC: str


class GeoSettings(BaseSettings):
    DADATA_API_KEY: str
    DADATA_SECRET_KEY: str


class AppSettings(SharedAppSettings):
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
        return hash_password_sync("dummy_password_for_timing_protection")


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
        extra="ignore",
    )


settings = Settings()
