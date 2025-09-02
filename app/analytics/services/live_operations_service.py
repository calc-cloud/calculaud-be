from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    LiveOperationFilterParams,
    ServiceTypeItem,
    ServiceTypesDistributionResponse,
    StatusesDistributionResponse,
    StatusItem,
)
from app.purposes.models import Purpose, StatusEnum
from app.service_types.models import ServiceType


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
