from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AnalyticsFilterParams,
    PurposeProcessingTimeByServiceType,
    PurposeProcessingTimeDistributionResponse,
    ServiceBreakdownItem,
    ServicesQuantityStackedResponse,
    ServiceTypeBreakdownItem,
    ServiceTypeStatusDistributionResponse,
    ServiceTypeWithBreakdownItem,
)
from app.analytics.utils import apply_analytics_filters
from app.purchases.models import Purchase
from app.purposes.models import (
    Purpose,
    PurposeContent,
    PurposeStatusHistory,
    StatusEnum,
)
from app.service_types.models import ServiceType
from app.services.models import Service
from app.stage_types.models import StageType
from app.stages.models import Stage


class AnalyticsService:
    """Service for handling analytics calculations and data aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def _get_date_diff_expression(self, end_date_col, start_date_col):
        """Get database-specific expression for calculating date difference in days."""
        # Detect database dialect
        dialect_name = self.db.bind.dialect.name

        if dialect_name == "postgresql":
            # PostgreSQL: Use DATE() cast and simple subtraction
            return func.date(end_date_col) - start_date_col
        elif dialect_name == "sqlite":
            # SQLite: Use JULIANDAY() for date arithmetic
            return func.julianday(func.date(end_date_col)) - func.julianday(
                start_date_col
            )
        else:
            # Fallback for other databases - try simple subtraction
            return func.date(end_date_col) - start_date_col

    def get_services_quantities(
        self, filters: AnalyticsFilterParams
    ) -> ServicesQuantityStackedResponse:
        """Get total quantities for each service type with service breakdown.

        Returns stacked bar chart data showing service types (x-axis) with service
        breakdowns (stack segments). Each service type includes:
        - total_quantity: Total quantity across all services in this service type
        - services: Array of services with their individual quantities

        Perfect for creating stacked bar charts with drill-down capability.
        """

        # Base query with joins - select service type, service, and quantity
        query = (
            select(
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                Service.id.label("service_id"),
                Service.name.label("service_name"),
                func.sum(PurposeContent.quantity).label("service_quantity"),
            )
            .select_from(Purpose)
            .join(PurposeContent, Purpose.id == PurposeContent.purpose_id)
            .join(Service, PurposeContent.service_id == Service.id)
            .join(ServiceType, Service.service_type_id == ServiceType.id)
        )

        # Apply analytics filters
        query = apply_analytics_filters(query, filters)

        # Group by both service type and service
        query = query.group_by(
            ServiceType.id, ServiceType.name, Service.id, Service.name
        ).order_by(ServiceType.name, Service.name)

        result = self.db.execute(query).all()

        # Process results to group by service type with service breakdown
        service_type_data = {}

        for row in result:
            service_type_key = (row.service_type_id, row.service_type_name)

            if service_type_key not in service_type_data:
                service_type_data[service_type_key] = {
                    "total_quantity": 0,
                    "services": [],
                }

            # Add service breakdown
            service_breakdown = ServiceBreakdownItem(
                service_id=row.service_id,
                service_name=row.service_name,
                quantity=int(row.service_quantity),
            )
            service_type_data[service_type_key]["services"].append(service_breakdown)
            service_type_data[service_type_key]["total_quantity"] += int(
                row.service_quantity
            )

        # Create final response
        service_type_items = []
        for (service_type_id, service_type_name), data in service_type_data.items():
            # Sort services by quantity descending
            sorted_services = sorted(
                data["services"], key=lambda x: x.quantity, reverse=True
            )
            service_type_item = ServiceTypeWithBreakdownItem(
                service_type_id=service_type_id,
                service_type_name=service_type_name,
                total_quantity=data["total_quantity"],
                services=sorted_services,
            )
            service_type_items.append(service_type_item)

        # Sort by service type ID for consistent ordering
        service_type_items.sort(key=lambda x: x.service_type_id)

        return ServicesQuantityStackedResponse(data=service_type_items)

    def get_service_type_status_distribution(
        self,
        target_status: StatusEnum,
        start_date: date | None = None,
        end_date: date | None = None,
        service_type_ids: list[int] | None = None,
    ) -> ServiceTypeStatusDistributionResponse:
        """
        Get service type distribution for purposes that changed to a specific status.

        Only counts the latest occurrence of the target status change per purpose
        within the specified timeframe.
        """

        # Subquery to find the latest status change per purpose for the target status
        latest_change_subquery = (
            select(
                PurposeStatusHistory.purpose_id,
                func.max(PurposeStatusHistory.changed_at).label("latest_change_at"),
            )
            .select_from(PurposeStatusHistory)
            .where(PurposeStatusHistory.new_status == target_status)
        )

        # Add date filtering to subquery
        if start_date:
            latest_change_subquery = latest_change_subquery.where(
                func.date(PurposeStatusHistory.changed_at) >= start_date
            )
        if end_date:
            latest_change_subquery = latest_change_subquery.where(
                func.date(PurposeStatusHistory.changed_at) <= end_date
            )

        latest_change_subquery = latest_change_subquery.group_by(
            PurposeStatusHistory.purpose_id
        ).subquery()

        # Main query to get service type distribution
        query = (
            select(
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                func.count(Purpose.id).label("count"),
            )
            .select_from(PurposeStatusHistory)
            .join(
                latest_change_subquery,
                and_(
                    PurposeStatusHistory.purpose_id
                    == latest_change_subquery.c.purpose_id,
                    PurposeStatusHistory.changed_at
                    == latest_change_subquery.c.latest_change_at,
                ),
            )
            .join(Purpose, PurposeStatusHistory.purpose_id == Purpose.id)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
            .where(PurposeStatusHistory.new_status == target_status)
        )

        # Add service type filtering
        if service_type_ids:
            query = query.where(ServiceType.id.in_(service_type_ids))

        # Group by service type and sort by count descending
        query = query.group_by(ServiceType.id, ServiceType.name).order_by(
            func.count(Purpose.id).desc()
        )

        result = self.db.execute(query).all()

        # Build response data
        service_type_items = []
        total_count = 0

        for row in result:
            service_type_item = ServiceTypeBreakdownItem(
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                count=row.count,
            )
            service_type_items.append(service_type_item)
            total_count += row.count

        return ServiceTypeStatusDistributionResponse(
            data=service_type_items,
            total_count=total_count,
            target_status=target_status,
        )

    def get_purpose_processing_time_distribution(
        self, params: AnalyticsFilterParams
    ) -> PurposeProcessingTimeDistributionResponse:
        """
        Get purpose processing time distribution by service type.

        Calculates processing time from first EMF ID stage creation to purpose completion.
        Filters by completion date range and groups results by service type.
        """

        # Subquery to get the earliest EMF ID stage creation date per purpose
        emf_start_subquery = (
            select(
                Stage.purchase_id,
                func.min(Stage.completion_date).label("emf_start_date"),
            )
            .select_from(Stage)
            .join(StageType, Stage.stage_type_id == StageType.id)
            .where(and_(StageType.name == "emf_id", Stage.completion_date.isnot(None)))
            .group_by(Stage.purchase_id)
        ).subquery()

        # Subquery to get the latest completion status change per purpose
        completion_subquery = (
            select(
                PurposeStatusHistory.purpose_id,
                func.max(PurposeStatusHistory.changed_at).label("completion_date"),
            )
            .select_from(PurposeStatusHistory)
            .where(PurposeStatusHistory.new_status == StatusEnum.COMPLETED)
            .group_by(PurposeStatusHistory.purpose_id)
        ).subquery()

        # Get database-specific date difference expression
        date_diff_expr = self._get_date_diff_expression(
            completion_subquery.c.completion_date, emf_start_subquery.c.emf_start_date
        )

        # Main query to calculate processing times
        query = (
            select(
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                func.count().label("count"),
                func.avg(date_diff_expr).label("avg_processing_days"),
                func.min(date_diff_expr).label("min_processing_days"),
                func.max(date_diff_expr).label("max_processing_days"),
            )
            .select_from(Purpose)
            .join(completion_subquery, Purpose.id == completion_subquery.c.purpose_id)
            .join(Purchase, Purpose.id == Purchase.purpose_id)
            .join(emf_start_subquery, Purchase.id == emf_start_subquery.c.purchase_id)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
        )

        # Apply analytics filters using completion date
        query = apply_analytics_filters(
            query, params, date_column=completion_subquery.c.completion_date
        )

        # Group by service type and sort by average processing time descending
        query = query.group_by(ServiceType.id, ServiceType.name).order_by(
            func.avg(date_diff_expr).desc()
        )

        result = self.db.execute(query).all()

        # Build response
        service_type_items = []
        total_purposes = 0

        for row in result:
            service_type_item = PurposeProcessingTimeByServiceType(
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                count=row.count,
                average_processing_days=round(float(row.avg_processing_days or 0), 2),
                min_processing_days=int(row.min_processing_days or 0),
                max_processing_days=int(row.max_processing_days or 0),
            )
            service_type_items.append(service_type_item)
            total_purposes += row.count

        return PurposeProcessingTimeDistributionResponse(
            service_types=service_type_items,
            total_purposes=total_purposes,
        )
