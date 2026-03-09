from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vocmesh"
    MQTT_BROKER_URL: str = "mqtt://localhost:1883"
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRY: int = 3600
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    BILLING_WEBHOOK_URL: str = ""
    ML_MODEL_PATH: str = "./ml_models"
    TENANT_ISOLATION_MODE: str = "row"
    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_prefix": "VOC_", "env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
