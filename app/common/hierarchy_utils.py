from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.hierarchies.models import Hierarchy

# Constants
EMPTY_RESULT_FILTER = -1  # Filter that never matches to return empty results


def build_hierarchy_filter(db: Session, hierarchy_ids: list[int], target_model_class):
    """
    Build recursive hierarchy filter for queries.

    This function builds a filter that matches all records belonging to the specified
    hierarchies OR any of their child hierarchies (recursive).

    Args:
        db: Database session
        hierarchy_ids: List of hierarchy IDs to filter by
        target_model_class: The model class that has hierarchy_id field (e.g., Purpose)

    Returns:
        SQLAlchemy filter condition that can be used in queries

    Example:
        # Filter purposes by hierarchy and all its children
        hierarchy_filter = build_hierarchy_filter(db, [1, 2], Purpose)
        query = query.filter(hierarchy_filter)
    """
    hierarchies_query = select(Hierarchy).where(Hierarchy.id.in_(hierarchy_ids))
    hierarchies = db.execute(hierarchies_query).scalars().all()

    if hierarchies:
        hierarchy_filters = []
        for hierarchy in hierarchies:
            # Use path LIKE to match hierarchy and all its children
            hierarchy_filters.append(Hierarchy.path.like(f"{hierarchy.path}%"))
        return or_(*hierarchy_filters)
    else:
        # If no hierarchies found, return empty result
        return target_model_class.id == EMPTY_RESULT_FILTER
