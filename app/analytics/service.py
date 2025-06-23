from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.filters import apply_filters
from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    FilterParams,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    HierarchyItem,
    ServicesQuantityResponse,
    ServiceTypesDistributionResponse,
    TimeSeriesDataset,
    TimeSeriesResponse,
)
from app.common.hierarchy_utils import build_hierarchy_filter
from app.config import settings
from app.costs.models import Cost, CurrencyEnum
from app.emfs.models import EMF
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.purposes.models import Purpose, PurposeContent
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

    def get_services_quantities(
        self, filters: FilterParams
    ) -> ServicesQuantityResponse:
        """Get total quantities for each service."""

        # Build query conditions manually for better control

        # Base query with joins
        query = (
            select(
                Service.name, func.sum(PurposeContent.quantity).label("total_quantity")
            )
            .select_from(Purpose)
            .join(PurposeContent, Purpose.id == PurposeContent.purpose_id)
            .join(Service, PurposeContent.service_id == Service.id)
        )

        query = apply_filters(
            query, filters, self.db, purpose_content_table_joined=True
        )

        # Group by service
        query = query.group_by(Service.id, Service.name).order_by(Service.name)

        result = self.db.execute(query).all()

        labels = [row.name for row in result]
        data = [float(row.total_quantity) for row in result]

        return ServicesQuantityResponse(labels=labels, data=data)

    def get_service_types_distribution(
        self, filters: FilterParams
    ) -> ServiceTypesDistributionResponse:
        """Get distribution of purposes by service type."""

        # Base query
        query = (
            select(ServiceType.name, func.count(Purpose.id).label("purpose_count"))
            .select_from(Purpose)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
        )

        # Apply filters
        query = apply_filters(query, filters, self.db)

        # Group by service type
        query = query.group_by(ServiceType.id, ServiceType.name).order_by(
            ServiceType.name
        )

        result = self.db.execute(query).all()

        labels = [row.name for row in result]
        data = [int(row.purpose_count) for row in result]

        return ServiceTypesDistributionResponse(labels=labels, data=data)

    def get_expenditure_timeline(
        self, filters: FilterParams, timeline_params: ExpenditureTimelineRequest
    ) -> TimeSeriesResponse:
        """Get expenditure over time with currency conversion."""

        # Determine date grouping
        if timeline_params.group_by == "day":
            date_trunc = func.date(Purpose.creation_time)
        elif timeline_params.group_by == "week":
            date_trunc = func.strftime("%Y-W%W", Purpose.creation_time)
        elif timeline_params.group_by == "year":
            date_trunc = func.strftime("%Y", Purpose.creation_time)
        else:  # month
            date_trunc = func.strftime("%Y-%m", Purpose.creation_time)

        # Base query with joins
        query = (
            select(
                date_trunc.label("time_period"),
                Cost.currency,
                func.sum(Cost.amount).label("total_amount"),
            )
            .select_from(Purpose)
            .join(EMF, Purpose.id == EMF.purpose_id)
            .join(Cost, EMF.id == Cost.emf_id)
        )

        # Apply filters
        query = apply_filters(query, filters, self.db)

        # Group by time period and currency
        query = query.group_by(date_trunc, Cost.currency).order_by(date_trunc)

        result = self.db.execute(query).all()

        # Process results and convert currency
        time_periods = set()
        currency_data = {}

        for row in result:
            time_periods.add(row.time_period)

            # Convert currency if needed
            converted_amount = self._convert_currency(
                row.total_amount, row.currency, timeline_params.currency
            )

            if row.time_period not in currency_data:
                currency_data[row.time_period] = 0

            currency_data[row.time_period] += converted_amount

        # Create response
        labels = sorted(list(time_periods))
        data = [currency_data.get(period, 0) for period in labels]

        dataset = TimeSeriesDataset(
            label=f"Expenditure ({timeline_params.currency.value})",
            data=data,
            currency=timeline_params.currency.value,
        )

        return TimeSeriesResponse(labels=labels, datasets=[dataset])

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
        hierarchy_query = (
            select(Hierarchy.id, Hierarchy.name, Hierarchy.path, Hierarchy.type)
            .select_from(Hierarchy)
            .where(hierarchy_condition)
            .order_by(Hierarchy.name)
        )
        hierarchy_query = apply_filters(hierarchy_query, filters, self.db)

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
