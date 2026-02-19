"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings sourced from environment variables or .env file."""

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
