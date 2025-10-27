from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

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
    smtp_user: str = ""
    smtp_pass: str = ""
    geoip_db_path: str

    jwt_private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    jwt_public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    jwt_algorithm: str = "RS256"
    
    @property
    def jwt_private_key(self) -> str:
        return self.jwt_private_key_path.read_text()

    @property
    def jwt_public_key(self) -> str:
        return self.jwt_public_key_path.read_text()
    
    prometheus_port: int = 8001
    log_level: str = "INFO"
    tz: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
    )

settings = Settings()