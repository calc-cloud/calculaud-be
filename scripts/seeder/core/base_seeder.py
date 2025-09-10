"""Abstract base class for all seeding operations."""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from scripts.seeder.core.session_manager import get_seeding_session
from scripts.seeder.utils.query_helpers import count_entities


class BaseSeeder(ABC):
    """
    Abstract base class for all seeding operations.

    Provides common functionality and enforces consistent interface
    across all seeder implementations.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the seeder.

        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose

    def log(self, message: str, prefix: str = "🔍") -> None:
        """
        Log a message if verbose mode is enabled.

        Args:
            message: Message to log
            prefix: Emoji prefix for the message
        """
        if self.verbose:
            print(f"{prefix} {message}")

    def run(self) -> dict[str, Any]:
        """
        Execute the seeding operation with proper session management.

        Returns:
            Dictionary containing seeding statistics and results
        """
        with get_seeding_session() as session:
            try:
                self.log(f"Starting {self.__class__.__name__}...")
                result = self.seed(session)
                session.commit()
                self.log(f"✅ {self.__class__.__name__} completed successfully!")
                return result
            except Exception as e:
                self.log(f"❌ Error in {self.__class__.__name__}: {e}", "🚨")
                session.rollback()
                raise

    @abstractmethod
    def seed(self, session: Session) -> dict[str, Any]:
        """
        Perform the actual seeding operation.

        Args:
            session: Database session to use for operations

        Returns:
            Dictionary containing seeding results and statistics
        """
        pass

    def get_existing_count(self, session: Session, model: type) -> int:
        """
        Get count of existing records for a model.

        Args:
            session: Database session
            model: SQLAlchemy model class

        Returns:
            Count of existing records
        """
        return count_entities(session, model)

    def should_skip(
        self, session: Session, model: type, skip_if_exists: bool = True
    ) -> bool:
        """
        Check if seeding should be skipped for a model.

        Args:
            session: Database session
            model: SQLAlchemy model class
            skip_if_exists: Whether to skip if records already exist

        Returns:
            True if seeding should be skipped
        """
        if not skip_if_exists:
            return False

        existing_count = self.get_existing_count(session, model)
        if existing_count > 0:
            self.log(
                f"Found {existing_count} existing {model.__name__} records, skipping..."
            )
            return True
        return False
