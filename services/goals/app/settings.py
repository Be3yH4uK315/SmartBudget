from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    db_url: str

class KafkaSettings(BaseSettings):
    kafka_bootstrap_servers: str
    kafka_goals_group_id: str
    kafka_topic_transaction_goal: str
    kafka_topic_budget_events: str
    kafka_topic_budget_notification: str

class ArqSettings(BaseSettings):
    redis_url: str
    arq_queue_name: str

class JWTSettings(BaseSettings):
    jwt_public_key: str
    jwt_algorithm: str
    jwt_audience: str

class AppSettings(BaseSettings):
    log_level: str
    tz: str
    frontend_url: str

class Settings(BaseSettings):
    db: DBSettings
    kafka: KafkaSettings
    arq: ArqSettings
    jwt: JWTSettings
    app: AppSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

settings = Settings()