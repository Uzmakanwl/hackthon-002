# app/db.py
"""Database engine and session management."""

from collections.abc import Generator

from sqlmodel import SQLModel, create_engine, Session

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create all SQLModel tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session
