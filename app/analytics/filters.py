from sqlalchemy import and_
from sqlalchemy.orm import Query

from app.analytics.schemas import FilterParams
from app.purposes.models import Purpose


def apply_filters(query: Query, filters: FilterParams) -> Query:
    """Apply universal filters to any query that includes Purpose."""

    conditions = []

    # Date range filter based on purpose creation_time
    if filters.start_date:
        conditions.append(Purpose.creation_time >= filters.start_date)

    if filters.end_date:
        conditions.append(Purpose.creation_time <= filters.end_date)

    # Hierarchy filter
    if filters.hierarchy_ids:
        conditions.append(Purpose.hierarchy_id.in_(filters.hierarchy_ids))

    # Status filter
    if filters.status:
        conditions.append(Purpose.status.in_(filters.status))

    # Supplier filter
    if filters.supplier_ids:
        conditions.append(Purpose.supplier_id.in_(filters.supplier_ids))

    # Service type filter (only applies to Purpose.service_type_id, not Service.service_type_id)
    if filters.service_type_ids:
        conditions.append(Purpose.service_type_id.in_(filters.service_type_ids))

    # Service filter (requires join with PurposeContent) - but only add join if not already present
    if filters.service_ids:
        from app.purposes.models import PurposeContent

        # Check if PurposeContent is already in the FROM clause of the query
        # If not, add the join
        try:
            # Try to add the join - SQLAlchemy will handle duplicate joins
            query = query.join(
                PurposeContent, Purpose.id == PurposeContent.purpose_id, isouter=False
            )
        except Exception:
            # If join already exists, continue
            pass
        conditions.append(PurposeContent.service_id.in_(filters.service_ids))

    # Apply all conditions
    if conditions:
        query = query.filter(and_(*conditions))

    return query
