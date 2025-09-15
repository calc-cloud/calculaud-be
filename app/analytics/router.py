from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    BudgetSourceCostDistributionResponse,
    LiveOperationFilterParams,
    PendingAuthoritiesDistributionResponse,
    PendingStagesStackedDistributionResponse,
    PurposeProcessingTimeDistributionResponse,
    PurposeProcessingTimeFilterParams,
    ServicesQuantityStackedResponse,
    ServiceTypeCostDistributionResponse,
    ServiceTypesDistributionResponse,
    ServiceTypeStatusDistributionResponse,
    StatusesDistributionResponse,
)
from app.analytics.services import AnalyticsService, LiveOperationsService
from app.analytics.services.financial_analytics_service import FinancialAnalyticsService
from app.database import get_db
from app.purposes.models import StatusEnum
from app.purposes.schemas import FilterParams

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


def get_live_operations_service(db: Session = Depends(get_db)) -> LiveOperationsService:
    """Dependency to get live operations service."""
    return LiveOperationsService(db)


def get_financial_analytics_service(
    db: Session = Depends(get_db),
) -> FinancialAnalyticsService:
    """Dependency to get financial analytics service."""
    return FinancialAnalyticsService(db)


@router.get(
    "/service-types/distribution", response_model=ServiceTypesDistributionResponse
)
def get_service_types_distribution(
    live_operations_service: Annotated[
        LiveOperationsService, Depends(get_live_operations_service)
    ],
    filters: Annotated[LiveOperationFilterParams, Query()],
) -> ServiceTypesDistributionResponse:
    """
    Get distribution of purposes by service type.

    Returns a pie chart showing purpose counts per service type.
    Supports service type filtering for live operations.
    """
    return live_operations_service.get_service_types_distribution(filters)


@router.get("/statuses/distribution", response_model=StatusesDistributionResponse)
def get_statuses_distribution(
    live_operations_service: Annotated[
        LiveOperationsService, Depends(get_live_operations_service)
    ],
    filters: Annotated[LiveOperationFilterParams, Query()],
) -> StatusesDistributionResponse:
    """
    Get distribution of purposes by status for live operations.

    Returns a pie chart showing purpose counts per status.
    Automatically excludes completed orders and supports service type filtering.
    """
    return live_operations_service.get_statuses_distribution(filters)


@router.get(
    "/pending-authorities/distribution",
    response_model=PendingAuthoritiesDistributionResponse,
)
def get_pending_authorities_distribution(
    live_operations_service: Annotated[
        LiveOperationsService, Depends(get_live_operations_service)
    ],
    filters: Annotated[LiveOperationFilterParams, Query()],
) -> PendingAuthoritiesDistributionResponse:
    """
    Get distribution of purposes by pending responsible authority for live operations.

    Returns a pie chart showing purpose counts per responsible authority.
    Shows which authority is responsible for the next action on each purpose.
    Automatically excludes completed orders and supports service type filtering.
    """
    return live_operations_service.get_pending_authorities_distribution(filters)


@router.get(
    "/pending-stages/distribution",
    response_model=PendingStagesStackedDistributionResponse,
)
def get_pending_stages_distribution(
    live_operations_service: Annotated[
        LiveOperationsService, Depends(get_live_operations_service)
    ],
    filters: Annotated[LiveOperationFilterParams, Query()],
) -> PendingStagesStackedDistributionResponse:
    """
    Get purchase workload distribution across stage types with service type breakdown.

    Returns stacked bar chart data showing stage types (x-axis) with service type
    breakdowns (stack segments). Each stage type includes:
    - total_count: Total number of purchases in this stage type
    - service_types: Array of service types with their individual counts

    A purchase with multiple pending stages at the same priority contributes to
    multiple stage type counts, with service type breakdown for each.
    Perfect for creating stacked bar charts with drill-down capability.
    Automatically excludes completed orders and supports service type filtering.
    """
    return live_operations_service.get_pending_stages_distribution(filters)


@router.get(
    "/service-types/{status}/distribution",
    response_model=ServiceTypeStatusDistributionResponse,
)
def get_service_type_status_distribution(
    status: StatusEnum,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            description="Filter by service type IDs",
            alias="service_type_id",
        ),
    ] = None,
) -> ServiceTypeStatusDistributionResponse:
    """
    Get service type distribution for purposes that changed to a specific status.

    Returns a pie chart showing purpose counts per service type for purposes that
    changed to the specified status within the given timeframe. For purposes that
    changed to the target status multiple times, only counts the latest occurrence.

    Path parameters:
    - status: The target status to analyze (e.g., COMPLETED, SIGNED)

    Query parameters:
    - start_date: Start date for filtering status changes (optional)
    - end_date: End date for filtering status changes (optional)
    - service_type_id: Filter by specific service type IDs (optional, can be repeated)

    Perfect for creating pie charts showing "How many purposes became COMPLETED
    in January, broken down by service type?"
    """
    return analytics_service.get_service_type_status_distribution(
        target_status=status,
        start_date=start_date,
        end_date=end_date,
        service_type_ids=service_type_ids,
    )


@router.get("/services/quantities", response_model=ServicesQuantityStackedResponse)
def get_services_quantities(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServicesQuantityStackedResponse:
    """
    Get service quantity distribution by service type with drill-down support.

    Returns stacked bar chart data showing service types (x-axis) with service
    breakdowns (stack segments). Each service type includes:
    - total_quantity: Total quantity across all services in this service type
    - services: Array of services with their individual quantities

    Perfect for creating stacked bar charts with drill-down capability.
    Supports all universal filters.
    """
    return analytics_service.get_services_quantities(filters)


@router.get(
    "/costs/distribution/by-service-type",
    response_model=ServiceTypeCostDistributionResponse,
)
def get_cost_distribution_by_service_type(
    financial_analytics_service: Annotated[
        FinancialAnalyticsService, Depends(get_financial_analytics_service)
    ],
    filters: Annotated[FilterParams, Query()],
) -> ServiceTypeCostDistributionResponse:
    """Get cost distribution by service type with multi-currency support."""
    return financial_analytics_service.get_cost_distribution_by_service_type(filters)


@router.get(
    "/costs/distribution/by-budget-source",
    response_model=BudgetSourceCostDistributionResponse,
)
def get_cost_distribution_by_budget_source(
    financial_analytics_service: Annotated[
        FinancialAnalyticsService, Depends(get_financial_analytics_service)
    ],
    filters: Annotated[FilterParams, Query()],
) -> BudgetSourceCostDistributionResponse:
    """Get cost distribution by budget source with multi-currency support."""
    return financial_analytics_service.get_cost_distribution_by_budget_source(filters)


@router.get(
    "/purposes/processing-times",
    response_model=PurposeProcessingTimeDistributionResponse,
)
def get_purpose_processing_time_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    params: Annotated[PurposeProcessingTimeFilterParams, Query()],
) -> PurposeProcessingTimeDistributionResponse:
    """
    Get purpose processing time distribution by service type.

    Calculates processing time from first EMF ID stage completion to purpose completion.
    Results grouped by service type with count, average, min, and max processing days.
    Supports date filtering by completion date.
    """
    return analytics_service.get_purpose_processing_time_distribution(params)
