from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.filters import apply_filters
from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    FilterParams,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    ServicesQuantityResponse,
    ServiceTypesDistributionResponse,
    TimeSeriesDataset,
    TimeSeriesResponse,
)
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
        from sqlalchemy import and_

        # Base query with joins
        query = (
            select(
                Service.name, func.sum(PurposeContent.quantity).label("total_quantity")
            )
            .select_from(Purpose)
            .join(PurposeContent, Purpose.id == PurposeContent.purpose_id)
            .join(Service, PurposeContent.service_id == Service.id)
        )

        # Apply filters manually
        conditions = []

        # Date range filter
        if filters.start_date:
            conditions.append(Purpose.creation_time >= filters.start_date)
        if filters.end_date:
            conditions.append(Purpose.creation_time <= filters.end_date)

        # Purpose-level filters
        if filters.hierarchy_ids:
            conditions.append(Purpose.hierarchy_id.in_(filters.hierarchy_ids))
        if filters.status:
            conditions.append(Purpose.status.in_(filters.status))
        if filters.supplier_ids:
            conditions.append(Purpose.supplier_id.in_(filters.supplier_ids))

        # Service filters
        if filters.service_ids:
            conditions.append(Service.id.in_(filters.service_ids))

        # Service type filter - join with ServiceType table
        if filters.service_type_ids:
            query = query.join(ServiceType, Service.service_type_id == ServiceType.id)
            conditions.append(ServiceType.id.in_(filters.service_type_ids))

        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))

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
        query = apply_filters(query, filters)

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
        query = apply_filters(query, filters)

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

        # Determine which hierarchy level to show
        if hierarchy_params.level is None:
            # Show top level (UNIT)
            target_level = HierarchyTypeEnum.UNIT
            parent_condition = Hierarchy.parent_id.is_(None)
        else:
            target_level = hierarchy_params.level
            if hierarchy_params.parent_id:
                parent_condition = Hierarchy.parent_id == hierarchy_params.parent_id
            else:
                parent_condition = Hierarchy.parent_id.is_(None)

        # Base query
        query = (
            select(Hierarchy.name, func.count(Purpose.id).label("purpose_count"))
            .select_from(Hierarchy)
            .join(Purpose, Hierarchy.id == Purpose.hierarchy_id, isouter=True)
            .filter(Hierarchy.type == target_level, parent_condition)
        )

        # Apply filters
        query = apply_filters(query, filters)

        # Group by hierarchy
        query = query.group_by(Hierarchy.id, Hierarchy.name).order_by(Hierarchy.name)

        result = self.db.execute(query).all()

        labels = [row.name for row in result]
        data = [int(row.purpose_count) for row in result]

        # Get parent name if drilling down
        parent_name = None
        if hierarchy_params.parent_id:
            parent = self.db.get(Hierarchy, hierarchy_params.parent_id)
            parent_name = parent.name if parent else None

        return HierarchyDistributionResponse(
            labels=labels, data=data, level=target_level, parent_name=parent_name
        )
