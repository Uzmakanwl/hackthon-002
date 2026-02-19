# app/config.py
"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings sourced from environment variables."""

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///./todo.db"
        )
        self.CORS_ORIGINS: str = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000"
        )
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
