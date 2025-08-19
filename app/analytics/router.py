from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    ServicesQuantityResponse,
    ServiceTypesDistributionResponse,
    TimelineExpenditureResponse,
)
from app.analytics.service import AnalyticsService
from app.database import get_db
from app.purposes.schemas import FilterParams

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


@router.get(
    "/services/quantities",
    response_model=ServicesQuantityResponse,
    operation_id="get_services_quantities",
)
def get_services_quantities(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServicesQuantityResponse:
    """Get total quantities procured for each service with filtering support."""
    return analytics_service.get_services_quantities(filters)


@router.get(
    "/service-types/distribution",
    response_model=ServiceTypesDistributionResponse,
    operation_id="get_service_types_distribution",
)
def get_service_types_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServiceTypesDistributionResponse:
    """Get procurement purpose distribution across service type categories."""
    return analytics_service.get_service_types_distribution(filters)


@router.get(
    "/expenditure/timeline",
    response_model=TimelineExpenditureResponse,
    operation_id="get_expenditure_timeline",
)
def get_expenditure_timeline(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[ExpenditureTimelineRequest, Query()],
) -> TimelineExpenditureResponse:
    """Get expenditure trends over time with multi-currency breakdown by service types."""
    return analytics_service.get_expenditure_timeline(request, request)


@router.get(
    "/hierarchies/distribution",
    response_model=HierarchyDistributionResponse,
    operation_id="get_hierarchy_distribution",
)
def get_hierarchy_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[HierarchyDistributionRequest, Query()],
) -> HierarchyDistributionResponse:
    """Get procurement distribution across organizational hierarchy with drill-down support."""
    return analytics_service.get_hierarchy_distribution(request, request)
