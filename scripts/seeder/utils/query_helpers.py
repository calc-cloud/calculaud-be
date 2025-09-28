"""Helper utilities for database queries in seeding operations."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session


def get_all_entities(session: Session, model: type) -> list[Any]:
    """
    Get all entities for a given model using SQLAlchemy v2 syntax.

    Args:
        session: Database session
        model: SQLAlchemy model class

    Returns:
        List of all model instances
    """
    stmt = select(model)
    return session.execute(stmt).scalars().all()


def get_entity_ids(session: Session, model: type) -> list[int]:
    """
    Get all IDs for a given model using SQLAlchemy v2 syntax.

    Args:
        session: Database session
        model: SQLAlchemy model class

    Returns:
        List of all model IDs
    """
    return [entity.id for entity in get_all_entities(session, model)]


def get_entity_by_attribute(
    session: Session, model: type, attribute_name: str, value: Any
) -> Any | None:
    """
    Get a single entity by attribute value using SQLAlchemy v2 syntax.

    Args:
        session: Database session
        model: SQLAlchemy model class
        attribute_name: Name of the attribute to filter by
        value: Value to match

    Returns:
        Single model instance or None if not found
    """
    attribute = getattr(model, attribute_name)
    stmt = select(model).where(attribute == value)
    return session.execute(stmt).scalars().first()


def get_entities_by_attribute(
    session: Session, model: type, attribute_name: str, value: Any
) -> list[Any]:
    """
    Get all entities by attribute value using SQLAlchemy v2 syntax.

    Args:
        session: Database session
        model: SQLAlchemy model class
        attribute_name: Name of the attribute to filter by
        value: Value to match

    Returns:
        List of matching model instances
    """
    attribute = getattr(model, attribute_name)
    stmt = select(model).where(attribute == value)
    return session.execute(stmt).scalars().all()


def count_entities(session: Session, model: type) -> int:
    """
    Count entities for a given model using efficient SQLAlchemy v2 syntax.

    Args:
        session: Database session
        model: SQLAlchemy model class

    Returns:
        Count of entities
    """
    stmt = select(model)
    result = session.execute(stmt)
    return len(result.scalars().all())
