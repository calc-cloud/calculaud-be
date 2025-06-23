from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    FilterParams,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    ServicesQuantityResponse,
    ServiceTypesDistributionResponse,
    TimeSeriesResponse,
)
from app.analytics.service import AnalyticsService
from app.database import get_db

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


@router.get("/services/quantities", response_model=ServicesQuantityResponse)
def get_services_quantities(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServicesQuantityResponse:
    """
    Get total quantities for each service.

    Returns a bar chart with services on x-axis and quantities on y-axis.
    Supports all universal filters.
    """
    return analytics_service.get_services_quantities(filters)


@router.get(
    "/service-types/distribution", response_model=ServiceTypesDistributionResponse
)
def get_service_types_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServiceTypesDistributionResponse:
    """
    Get distribution of purposes by service type.

    Returns a pie chart showing purpose counts per service type.
    Supports all universal filters.
    """
    return analytics_service.get_service_types_distribution(filters)


@router.get("/expenditure/timeline", response_model=TimeSeriesResponse)
def get_expenditure_timeline(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[ExpenditureTimelineRequest, Query()],
) -> TimeSeriesResponse:
    """
    Get expenditure over time with currency conversion.

    Returns a line chart with time on x-axis and expenditure on y-axis.
    Supports currency switching (ILS/USD) and service type filtering.
    Supports all universal filters.
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
