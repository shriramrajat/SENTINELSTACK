import os
from typing import Optional
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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI / LLM Integration
    # If not provided, AIService will use MockLLM
    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        # env_file_encoding = 'utf-8' # Optional but good practice
        case_sensitive = True

# Global settings instance
settings = Settings()