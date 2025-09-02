from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app import Purchase
from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    HierarchyItem,
    ServiceItem,
    ServicesQuantityResponse,
    ServiceTypeExpenditureItem,
    TimelineExpenditureItem,
    TimelineExpenditureResponse,
)
from app.common.hierarchy_utils import build_hierarchy_filter
from app.config import settings
from app.costs.models import Cost, CurrencyEnum
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.purposes.filters import apply_filters
from app.purposes.models import Purpose, PurposeContent
from app.purposes.schemas import FilterParams
from app.service_types.models import ServiceType
from app.services.models import Service


class AnalyticsService:
    """Service for handling analytics calculations and data aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def _convert_currency(
        self, amount: float, from_currency: CurrencyEnum, to_currency: CurrencyEnum
    ) -> float:
        """Convert currency using the configured rate."""
        if from_currency == to_currency:
            return amount

        # Convert USD amounts
        if from_currency in [CurrencyEnum.SUPPORT_USD, CurrencyEnum.AVAILABLE_USD]:
            if to_currency == CurrencyEnum.ILS:
                return amount * settings.usd_to_ils_rate

        # Convert ILS amounts
        elif from_currency == CurrencyEnum.ILS:
            if to_currency in [CurrencyEnum.SUPPORT_USD, CurrencyEnum.AVAILABLE_USD]:
                return amount / settings.usd_to_ils_rate

        return amount

    def _get_date_format_function(self, column, group_by: str):
        """Get database-specific date formatting function."""
        # Detect database type from the dialect
        dialect_name = self.db.bind.dialect.name

        if dialect_name == "postgresql":
            # PostgreSQL uses to_char
            if group_by == "day":
                return func.to_char(column, "YYYY-MM-DD")
            elif group_by == "week":
                return func.to_char(column, 'YYYY-"W"WW')
            elif group_by == "year":
                return func.to_char(column, "YYYY")
            else:  # month
                return func.to_char(column, "YYYY-MM")
        else:
            # SQLite and others use strftime
            if group_by == "day":
                return func.strftime("%Y-%m-%d", column)
            elif group_by == "week":
                return func.strftime("%Y-W%W", column)
            elif group_by == "year":
                return func.strftime("%Y", column)
            else:  # month
                return func.strftime("%Y-%m", column)

    def get_services_quantities(
        self, filters: FilterParams
    ) -> ServicesQuantityResponse:
        """Get total quantities for each service."""

        # Build query conditions manually for better control

        # Base query with joins - select all Service fields, ServiceType name, and quantity
        query = (
            select(
                Service.id,
                Service.name,
                Service.service_type_id,
                ServiceType.name.label("service_type_name"),
                func.sum(PurposeContent.quantity).label("total_quantity"),
            )
            .select_from(Purpose)
            .join(PurposeContent, Purpose.id == PurposeContent.purpose_id)
            .join(Service, PurposeContent.service_id == Service.id)
            .join(ServiceType, Service.service_type_id == ServiceType.id)
        )

        query = apply_filters(
            query, filters, self.db, purpose_content_table_joined=True
        )

        # Group by service
        query = query.group_by(
            Service.id, Service.name, Service.service_type_id, ServiceType.name
        ).order_by(Service.name)

        result = self.db.execute(query).all()

        # Create ServiceItem objects
        service_items = []
        for row in result:
            service_item = ServiceItem(
                id=row.id,
                name=row.name,
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                quantity=float(row.total_quantity),
            )
            service_items.append(service_item)

        return ServicesQuantityResponse(data=service_items)

    def get_expenditure_timeline(
        self, filters: FilterParams, timeline_params: ExpenditureTimelineRequest
    ) -> TimelineExpenditureResponse:
        """Get expenditure over time with service type breakdown."""

        # Determine date grouping using database-specific function
        date_trunc = self._get_date_format_function(
            Purpose.creation_time, timeline_params.group_by
        )

        # Base query with ServiceType joins
        query = (
            select(
                date_trunc.label("time_period"),
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                Cost.currency,
                func.sum(Cost.amount).label("total_amount"),
            )
            .select_from(Purpose)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
            .join(Purchase, Purpose.id == Purchase.purpose_id)
            .join(Cost, Purchase.id == Cost.purchase_id)
        )

        # Apply filters
        query = apply_filters(query, filters, self.db)

        # Group by time period, service type, and currency
        query = query.group_by(
            date_trunc, ServiceType.id, ServiceType.name, Cost.currency
        ).order_by(date_trunc, ServiceType.name)

        result = self.db.execute(query).all()

        # Process results by time_period → service_type → currency
        time_periods = set()
        period_data = {}

        for row in result:
            time_periods.add(row.time_period)

            if row.time_period not in period_data:
                period_data[row.time_period] = {}

            service_key = (row.service_type_id, row.service_type_name)
            if service_key not in period_data[row.time_period]:
                period_data[row.time_period][service_key] = {
                    CurrencyEnum.ILS: 0.0,
                    CurrencyEnum.SUPPORT_USD: 0.0,
                    CurrencyEnum.AVAILABLE_USD: 0.0,
                }

            period_data[row.time_period][service_key][row.currency] = float(
                row.total_amount
            )

        # Create response with service type breakdown
        items = []

        for period in sorted(time_periods):
            service_data = []
            period_total_ils = 0.0
            period_total_usd = 0.0

            for (service_type_id, service_type_name), amounts in period_data[
                period
            ].items():
                ils_amount = amounts.get(CurrencyEnum.ILS, 0.0)
                support_usd_amount = amounts.get(CurrencyEnum.SUPPORT_USD, 0.0)
                available_usd_amount = amounts.get(CurrencyEnum.AVAILABLE_USD, 0.0)

                # Calculate totals for this service type
                usd_subtotal = support_usd_amount + available_usd_amount
                service_total_usd = usd_subtotal + (
                    ils_amount / settings.usd_to_ils_rate
                )
                service_total_ils = ils_amount + (
                    usd_subtotal * settings.usd_to_ils_rate
                )

                # Add to period totals
                period_total_usd += service_total_usd
                period_total_ils += service_total_ils

                service_item = ServiceTypeExpenditureItem(
                    service_type_id=service_type_id,
                    name=service_type_name,
                    total_ils=service_total_ils,
                    total_usd=service_total_usd,
                )
                service_data.append(service_item)

            # Sort service data by name for consistent ordering
            service_data.sort(key=lambda x: x.name)

            timeline_item = TimelineExpenditureItem(
                time_period=period,
                total_ils=period_total_ils,
                total_usd=period_total_usd,
                data=service_data,
            )
            items.append(timeline_item)

        return TimelineExpenditureResponse(
            items=items, group_by=timeline_params.group_by
        )

    def get_hierarchy_distribution(
        self, filters: FilterParams, hierarchy_params: HierarchyDistributionRequest
    ) -> HierarchyDistributionResponse:
        """Get distribution of purposes by hierarchy with drill-down support."""

        target_level = None

        # Apply hierarchy conditions according to requirements
        if (
            hierarchy_params.parent_id is not None
            and hierarchy_params.level is not None
        ):
            # Get children of parent (recursively) at specified level
            target_level = hierarchy_params.level

            # Get parent hierarchy to use its path
            parent_hierarchy = self.db.get(Hierarchy, hierarchy_params.parent_id)
            if not parent_hierarchy:
                return HierarchyDistributionResponse(
                    items=[], level=target_level, parent_name=None
                )

            # Get all descendants of parent that are at the target level
            descendants_query = (
                select(Hierarchy.id)
                .select_from(Hierarchy)
                .where(
                    Hierarchy.type == target_level,
                    Hierarchy.path.like(f"{parent_hierarchy.path}%"),
                )
            )
            descendant_ids = [
                row.id for row in self.db.execute(descendants_query).all()
            ]

            hierarchy_condition = Hierarchy.id.in_(descendant_ids)

        elif hierarchy_params.parent_id is not None and hierarchy_params.level is None:
            # Get all direct children of parent
            hierarchy_condition = Hierarchy.parent_id == hierarchy_params.parent_id

        else:
            # parent_id is None - get all hierarchies of specified level (or UNIT if None)
            if hierarchy_params.level is not None:
                target_level = hierarchy_params.level
            else:
                target_level = HierarchyTypeEnum.UNIT

            hierarchy_condition = Hierarchy.type == target_level

        # Base query to get hierarchy nodes
        conditions = [hierarchy_condition]
        if filters.hierarchy_ids:
            conditions.append(
                build_hierarchy_filter(self.db, filters.hierarchy_ids, Hierarchy)
            )

        hierarchy_query = (
            select(
                Hierarchy.id,
                Hierarchy.name,
                Hierarchy.path,
                Hierarchy.type,
                Hierarchy.parent_id,
            )
            .select_from(Hierarchy)
            .where(and_(*conditions))
            .order_by(Hierarchy.name)
        )

        hierarchy_result = self.db.execute(hierarchy_query).all()

        # For each hierarchy node, count purposes in its entire subtree
        items = []

        for row in hierarchy_result:
            # Count purposes in this hierarchy's subtree (including direct purposes)
            subtree_filter = build_hierarchy_filter(self.db, [row.id], Purpose)

            subtree_query = (
                select(func.count(Purpose.id))
                .select_from(Purpose)
                .join(Hierarchy, Purpose.hierarchy_id == Hierarchy.id)
                .where(subtree_filter)
            )

            # Apply the same filters to subtree count using apply_filters function
            filtered_query = apply_filters(
                subtree_query, filters, self.db, hierarchy_table_joined=True
            )

            subtree_count = self.db.execute(filtered_query).scalar() or 0

            # Create hierarchy item with all details
            hierarchy_item = HierarchyItem(
                id=row.id,
                name=row.name,
                path=row.path,
                type=row.type,
                count=int(subtree_count),
                parent_id=row.parent_id,
            )
            items.append(hierarchy_item)

        # Get parent name if drilling down
        parent_name = None
        if hierarchy_params.parent_id:
            parent = self.db.get(Hierarchy, hierarchy_params.parent_id)
            parent_name = parent.name if parent else None

        return HierarchyDistributionResponse(
            items=items, level=target_level, parent_name=parent_name
        )
