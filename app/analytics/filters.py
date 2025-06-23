from sqlalchemy import Select, and_
from sqlalchemy.orm import Session

from app.analytics.schemas import FilterParams
from app.common.hierarchy_utils import build_hierarchy_filter
from app.hierarchies.models import Hierarchy
from app.purposes.models import Purpose, PurposeContent


def apply_filters(
    query: Select,
    filters: FilterParams,
    db: Session = None,
    *,
    hierarchy_table_joined: bool = False,
    purpose_content_table_joined: bool = False
) -> Select:
    """Apply universal filters to any query that includes Purpose."""

    conditions = []

    # Date range filter based on purpose creation_time
    if filters.start_date:
        conditions.append(Purpose.creation_time >= filters.start_date)

    if filters.end_date:
        conditions.append(Purpose.creation_time <= filters.end_date)

    # Recursive hierarchy filter - requires join with Hierarchy table
    if filters.hierarchy_ids:
        if not hierarchy_table_joined:
            query = query.join(Hierarchy, Purpose.hierarchy_id == Hierarchy.id)
        hierarchy_filter = build_hierarchy_filter(db, filters.hierarchy_ids, Purpose)
        conditions.append(hierarchy_filter)

    # Status filter
    if filters.status:
        conditions.append(Purpose.status.in_(filters.status))

    # Supplier filter
    if filters.supplier_ids:
        conditions.append(Purpose.supplier_id.in_(filters.supplier_ids))

    # Service type filter
    if filters.service_type_ids:
        conditions.append(Purpose.service_type_id.in_(filters.service_type_ids))

    # Service filter - requires join with PurposeContent
    if filters.service_ids:
        if not purpose_content_table_joined:
            query = query.join(PurposeContent, Purpose.id == PurposeContent.purpose_id)
        conditions.append(PurposeContent.service_id.in_(filters.service_ids))

    # Apply all conditions
    if conditions:
        query = query.where(and_(*conditions))

    return query
