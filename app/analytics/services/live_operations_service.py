from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    LiveOperationFilterParams,
    PendingAuthoritiesDistributionResponse,
    PendingAuthorityItem,
    PendingStagesStackedDistributionResponse,
    PendingStageWithBreakdownItem,
    ServiceTypeBreakdownItem,
    ServiceTypeItem,
    ServiceTypesDistributionResponse,
    StatusesDistributionResponse,
    StatusItem,
)
from app.purchases.models import Purchase
from app.purposes.models import Purpose, StatusEnum
from app.purposes.pending_authority_utils import get_pending_authority_id_query
from app.responsible_authorities.models import ResponsibleAuthority
from app.service_types.models import ServiceType
from app.stage_types.models import StageType
from app.stages.models import Stage


def _apply_filters(query: Select, filters: LiveOperationFilterParams) -> Select:
    """Apply live operation filters to any query."""

    # Filter out completed orders for live operations
    conditions = [Purpose.status != StatusEnum.COMPLETED]

    # Service type filter
    if filters.service_type_ids:
        conditions.append(Purpose.service_type_id.in_(filters.service_type_ids))

    if conditions:
        query = query.where(*conditions)

    return query


class LiveOperationsService:
    """Service for handling live operations analytics and data aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def get_service_types_distribution(
        self, filters: LiveOperationFilterParams
    ) -> ServiceTypesDistributionResponse:
        """Get distribution of purposes by service type."""

        # Base query - select all ServiceType fields and count
        query = (
            select(
                ServiceType.id,
                ServiceType.name,
                func.count(Purpose.id).label("purpose_count"),
            )
            .select_from(Purpose)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
        )

        # Apply filters
        query = _apply_filters(query, filters)

        # Group by service type
        query = query.group_by(ServiceType.id, ServiceType.name).order_by(
            ServiceType.name
        )

        result = self.db.execute(query).all()

        # Create ServiceTypeItem objects
        service_type_items = []
        for row in result:
            service_type_item = ServiceTypeItem(
                id=row.id,
                name=row.name,
                count=int(row.purpose_count),
            )
            service_type_items.append(service_type_item)

        return ServiceTypesDistributionResponse(data=service_type_items)

    def get_statuses_distribution(
        self, filters: LiveOperationFilterParams
    ) -> StatusesDistributionResponse:
        """Get distribution of purposes by status (excluding completed)."""

        # Base query - select status and count
        query = select(
            Purpose.status,
            func.count(Purpose.id).label("purpose_count"),
        ).select_from(Purpose)

        # Apply filters
        query = _apply_filters(query, filters)

        # Group by status
        query = query.group_by(Purpose.status).order_by(Purpose.status)

        result = self.db.execute(query).all()

        # Create StatusItem objects
        status_items = []
        for row in result:
            status_item = StatusItem(
                status=row.status.value,  # Convert enum to string
                count=int(row.purpose_count),
            )
            status_items.append(status_item)

        return StatusesDistributionResponse(data=status_items)

    def get_pending_authorities_distribution(
        self, filters: LiveOperationFilterParams
    ) -> PendingAuthoritiesDistributionResponse:
        """Get distribution of purposes by pending responsible authority."""

        # Build query using pending authority subquery
        pending_authority_subquery = get_pending_authority_id_query(Purpose.id)

        # Base query - select authority info and count purposes
        query = (
            select(
                pending_authority_subquery.label("authority_id"),
                ResponsibleAuthority.name.label("authority_name"),
                func.count(Purpose.id).label("purpose_count"),
            )
            .select_from(Purpose)
            .outerjoin(
                ResponsibleAuthority,
                ResponsibleAuthority.id == pending_authority_subquery,
            )
        )

        # Apply filters
        query = _apply_filters(query, filters)

        # Group by authority
        query = query.group_by(
            pending_authority_subquery, ResponsibleAuthority.name
        ).order_by(ResponsibleAuthority.name.nulls_last())

        result = self.db.execute(query).all()

        # Create PendingAuthorityItem objects
        authority_items = []
        for row in result:
            authority_item = PendingAuthorityItem(
                authority_id=row.authority_id,
                authority_name=row.authority_name or "No Pending Authority",
                count=int(row.purpose_count),
            )
            authority_items.append(authority_item)

        return PendingAuthoritiesDistributionResponse(data=authority_items)

    def get_pending_stages_distribution(
        self, filters: LiveOperationFilterParams
    ) -> PendingStagesStackedDistributionResponse:
        """Get purchase workload distribution across stage types with service type breakdown.

        Returns stage type counts with service type breakdown for stacked bar charts.
        Each stage type includes total count and detailed breakdown by service types.
        A purchase with multiple pending stages at the same priority contributes to
        multiple stage type counts, with service type breakdown for each.
        """

        # Subquery to find the current priority for each purchase (with live operations filters)
        subquery = (
            select(
                Purchase.id.label("purchase_id"),
                Stage.priority.label("priority_value"),
            )
            .select_from(Purchase)
            .join(Purpose, Purchase.purpose_id == Purpose.id)
            .join(Stage, Purchase.id == Stage.purchase_id)
            .join(StageType, Stage.stage_type_id == StageType.id)
            .where(
                Stage.completion_date.is_(None),  # Only incomplete stages
            )
            .order_by(
                Purchase.id,
                Stage.priority.asc(),  # Lowest priority number = highest priority
                StageType.id.asc(),  # Tie-breaker
            )
            .distinct(
                Purchase.id
            )  # Get only the first (highest priority) incomplete stage per purchase
        )

        # Apply live operations filters to subquery using the centralized function
        subquery = _apply_filters(subquery, filters)
        current_priority_subquery = subquery.cte("current_priority")

        # Main query: count stages at current priority level grouped by stage type AND service type
        query = (
            select(
                StageType.id.label("stage_type_id"),
                StageType.name.label("stage_type_name"),
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                func.count(Stage.id).label("stage_count"),
            )
            .select_from(Purpose)
            .join(Purchase, Purpose.id == Purchase.purpose_id)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
            .join(Stage, Purchase.id == Stage.purchase_id)
            .join(StageType, Stage.stage_type_id == StageType.id)
            .join(
                current_priority_subquery,
                current_priority_subquery.c.purchase_id == Purchase.id,
            )
            .where(
                Stage.completion_date.is_(None),  # Only incomplete stages
                # Stage must be at current priority level
                Stage.priority == current_priority_subquery.c.priority_value,
            )
        )

        # Group by both stage type and service type
        query = query.group_by(
            StageType.id, StageType.name, ServiceType.id, ServiceType.name
        ).order_by(StageType.name, ServiceType.name)

        result = self.db.execute(query).all()

        # Process results to group by stage type with service type breakdown
        stage_type_data = {}

        for row in result:
            stage_key = (row.stage_type_id, row.stage_type_name)

            if stage_key not in stage_type_data:
                stage_type_data[stage_key] = {"total_count": 0, "service_types": []}

            # Add service type breakdown
            service_breakdown = ServiceTypeBreakdownItem(
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                count=int(row.stage_count),
            )
            stage_type_data[stage_key]["service_types"].append(service_breakdown)
            stage_type_data[stage_key]["total_count"] += int(row.stage_count)

        # Create final response
        stage_items = []
        for (stage_type_id, stage_type_name), data in stage_type_data.items():
            stage_item = PendingStageWithBreakdownItem(
                stage_type_id=stage_type_id,
                stage_type_name=stage_type_name,
                total_count=data["total_count"],
                service_types=data["service_types"],
            )
            stage_items.append(stage_item)

        # Sort by stage type ID for consistent ordering
        stage_items.sort(key=lambda x: x.stage_type_id or 0)

        return PendingStagesStackedDistributionResponse(data=stage_items)
