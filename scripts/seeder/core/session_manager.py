"""Database session management for seeding operations."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal


@contextmanager
def get_seeding_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions during seeding operations.

    Provides proper session lifecycle management with automatic rollback
    on exceptions and cleanup on completion.

    Yields:
        Session: SQLAlchemy session for database operations

    Raises:
        Exception: Any database-related exception during seeding
    """
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
