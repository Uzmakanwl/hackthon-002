# app/config.py
"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment."""

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
