"""Database engine and session management."""

from collections.abc import AsyncGenerator

from sqlmodel import Session, create_engine

from app.config import get_settings

engine = create_engine(get_settings().DATABASE_URL, echo=False)


def get_session() -> AsyncGenerator[Session, None]:
    """Yield a SQLModel session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session
