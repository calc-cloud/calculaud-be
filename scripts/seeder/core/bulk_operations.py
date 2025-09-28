"""Bulk operations utilities for efficient database seeding."""

from itertools import islice
from typing import Any, Iterable, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


class BulkInserter:
    """Utility class for performing efficient bulk insert operations."""

    def __init__(self, session: Session, batch_size: int = 1000):
        """
        Initialize the bulk inserter.

        Args:
            session: Database session to use
            batch_size: Number of records to insert per batch
        """
        self.session = session
        self.batch_size = batch_size

    def insert_models(self, models: list[T]) -> int:
        """
        Insert a list of model instances in batches.

        Args:
            models: List of SQLAlchemy model instances to insert

        Returns:
            Number of records inserted

        Raises:
            ValueError: If models list is invalid
        """
        if not models:
            return 0

        if not isinstance(models, list):
            raise ValueError("models must be a list")

        total_inserted = 0

        try:
            for i in range(0, len(models), self.batch_size):
                batch = models[i : i + self.batch_size]
                self.session.add_all(batch)

                # Only flush if we need IDs for foreign key relationships
                if i + self.batch_size < len(models):
                    self.session.flush()

                total_inserted += len(batch)
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to insert models: {e}") from e

        return total_inserted

    def insert_from_data(
        self, model_class: type[T], data_list: list[dict[str, Any]]
    ) -> int:
        """
        Create and insert model instances from data dictionaries.

        Args:
            model_class: SQLAlchemy model class
            data_list: List of dictionaries containing model data

        Returns:
            Number of records inserted

        Raises:
            ValueError: If data_list is invalid or model_class is None
            RuntimeError: If model creation or insertion fails
        """
        if not data_list:
            return 0

        if model_class is None:
            raise ValueError("model_class cannot be None")

        if not isinstance(data_list, list):
            raise ValueError("data_list must be a list")

        try:
            models = [model_class(**data) for data in data_list]
            return self.insert_models(models)
        except TypeError as e:
            raise RuntimeError(
                f"Failed to create {model_class.__name__} instances: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to insert {model_class.__name__} data: {e}"
            ) from e

    def create_with_explicit_ids(
        self, model_class: type[T], data_list: list[dict[str, Any]]
    ) -> list[T]:
        """
        Create models with explicit IDs and handle sequence synchronization.

        This method is useful for seeding reference data that needs specific IDs
        (like stage types or predefined flows from backup data).

        Args:
            model_class: SQLAlchemy model class
            data_list: List of dictionaries containing model data with explicit IDs

        Returns:
            List of created model instances
        """
        if not data_list:
            return []

        models = []
        for data in data_list:
            # Create model with explicit ID
            model = model_class(**data)
            models.append(model)

        # Insert in batches
        self.insert_models(models)

        return models


def chunked(iterable: Iterable[T], chunk_size: int) -> Iterable[list[T]]:
    """
    Split an iterable into chunks of specified size.

    Args:
        iterable: Iterable to chunk
        chunk_size: Size of each chunk

    Yields:
        Lists containing chunks of the original iterable
    """
    iterator = iter(iterable)
    while True:
        chunk = list(islice(iterator, chunk_size))
        if not chunk:
            break
        yield chunk


def batch_process(items: list[T], batch_size: int = 1000) -> Iterable[list[T]]:
    """
    Process a list in batches.

    Args:
        items: List of items to process
        batch_size: Size of each batch

    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
