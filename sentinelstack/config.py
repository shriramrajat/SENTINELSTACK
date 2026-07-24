import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SentinelStack v1"
    ENV: str = "development"

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://sentinel_user:sentinel_password@localhost:5432/sentinel_db"

    # Cache (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "unsafe-development-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    # Operational & Logic Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    INCIDENT_THRESHOLD_LATENCY_MS: float = 2000.0
    INCIDENT_THRESHOLD_ERROR_RATE: float = 10.0
    
    # Alerting
    WEBHOOK_URL: Optional[str] = None

    # AI / LLM Integration
    # If not provided, AIService will use MockLLM
    OPENAI_API_KEY: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def coerce_database_url(cls, v: str) -> str:
        """
        Fly.io Postgres injects DATABASE_URL as 'postgres://...'
        SQLAlchemy's asyncpg driver requires 'postgresql+asyncpg://...'
        This validator silently fixes it so the app works on Fly without
        needing to manually override the secret after every Postgres attach.
        """
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://") and "+asyncpg" not in v:
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()