from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    LiveOperationFilterParams,
    PendingAuthoritiesDistributionResponse,
    PendingStagesStackedDistributionResponse,
    ServicesQuantityStackedResponse,
    ServiceTypesDistributionResponse,
    StatusesDistributionResponse,
    TimelineExpenditureResponse,
)
from app.analytics.services import AnalyticsService, LiveOperationsService
from app.database import get_db
from app.purposes.schemas import FilterParams

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


def get_live_operations_service(db: Session = Depends(get_db)) -> LiveOperationsService:
    """Dependency to get live operations service."""
    return LiveOperationsService(db)


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


@router.get("/expenditure/timeline", response_model=TimelineExpenditureResponse)
def get_expenditure_timeline(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[ExpenditureTimelineRequest, Query()],
) -> TimelineExpenditureResponse:
    """
    Get expenditure over time with service type breakdown.

    Returns expenditure data grouped by time periods, with detailed breakdown
    by service type for each period. Each item includes:
    - time_period: The grouped time period (e.g., "2024-01")
    - total_ils: Total expenditure in ILS for the period
    - total_usd: Total expenditure in USD for the period
    - data: Array of service types with their expenditure amounts

    Supports all universal filters and time grouping (day, week, month, year).
    """
    return analytics_service.get_expenditure_timeline(request, request)


@router.get("/hierarchies/distribution", response_model=HierarchyDistributionResponse)
def get_hierarchy_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[HierarchyDistributionRequest, Query()],
) -> HierarchyDistributionResponse:
    """
    Get distribution of purposes by hierarchy with drill-down support.

    Returns a pie chart showing purpose counts per hierarchy level.
    Supports drill-down navigation through hierarchy levels:
    UNIT → CENTER → ANAF → MADOR → TEAM

    Query parameters:
    - level: Hierarchy level to display (optional, defaults to UNIT)
    - parent_id: Parent hierarchy ID for drill-down (optional)

    Supports all universal filters.
    """
    return analytics_service.get_hierarchy_distribution(request, request)
