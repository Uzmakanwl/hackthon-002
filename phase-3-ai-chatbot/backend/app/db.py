"""Database connection and session management."""

from collections.abc import Generator

from sqlmodel import SQLModel, create_engine, Session

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create all database tables from SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Yields:
        Session: A SQLModel database session that auto-closes after use.
    """
    with Session(engine) as session:
        yield session


def get_session_sync() -> Session:
    """Return a synchronous database session (for MCP tools).

    Returns:
        Session: A SQLModel database session. Caller is responsible for closing.
    """
    return Session(engine)
