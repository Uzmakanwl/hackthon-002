# tests/test_db.py
import pytest
from app.config import get_settings


class TestConfig:
    def test_settings_loads(self):
        settings = get_settings()
        assert settings.DATABASE_URL is not None
        assert settings.CORS_ORIGINS is not None

    def test_database_url_is_string(self):
        settings = get_settings()
        assert isinstance(settings.DATABASE_URL, str)
