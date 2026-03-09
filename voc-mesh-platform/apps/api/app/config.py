from functools import lru_cache

from pydantic import field_validator
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

    @field_validator("DATABASE_URL")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        """DigitalOcean provides postgresql:// but SQLAlchemy async needs +asyncpg."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    model_config = {"env_prefix": "VOC_", "env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
