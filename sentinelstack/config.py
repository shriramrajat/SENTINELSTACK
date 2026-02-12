import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SentinelStack v1"
    ENV: str = "development"
    
    # Database (PostgreSQL)
    # Default points to localhost for local dev outside docker, 
    # or use 'db' hostname if running app inside docker.
    DATABASE_URL: str = "postgresql+asyncpg://sentinel_user:sentinel_password@localhost:5432/sentinel_db"
    
    # Cache (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security (We will rotate this later)
    SECRET_KEY: str = "unsafe-development-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()