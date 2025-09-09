from sqlalchemy import Select, and_, func
from sqlalchemy.orm import Session

from app.common.hierarchy_utils import build_hierarchy_filter
from app.hierarchies.models import Hierarchy
from app.purposes.models import Purpose, PurposeContent
from app.purposes.pending_authority_utils import get_pending_authority_id_query
from app.purposes.schemas import FilterParams


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
        conditions.append(func.date(Purpose.creation_time) >= filters.start_date)

    if filters.end_date:
        conditions.append(func.date(Purpose.creation_time) <= filters.end_date)

    # Recursive hierarchy filter - requires join with Hierarchy table
    if filters.hierarchy_ids:
        if not hierarchy_table_joined:
            query = query.join(Hierarchy, Purpose.hierarchy_id == Hierarchy.id)
        hierarchy_filter = build_hierarchy_filter(db, filters.hierarchy_ids, Purpose)
        conditions.append(hierarchy_filter)

    # Status filter
    if filters.statuses:
        conditions.append(Purpose.status.in_(filters.statuses))

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

    # Pending authority filter - using correlated subquery
    # NOTE: Must use the same logic as Purpose.pending_authority property
    if filters.pending_authorities:
        pending_authority_subq = get_pending_authority_id_query(Purpose.id)
        conditions.append(pending_authority_subq.in_(filters.pending_authorities))

    # Flagged filter
    if filters.is_flagged is not None:
        conditions.append(Purpose.is_flagged == filters.is_flagged)

    # Apply all conditions
    if conditions:
        query = query.where(and_(*conditions))

    return query
