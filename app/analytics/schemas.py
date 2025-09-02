from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field

from app.hierarchies.models import HierarchyTypeEnum
from app.hierarchies.schemas import Hierarchy
from app.purposes.schemas import FilterParams
from app.service_types.schemas import ServiceType
from app.services.schemas import Service


class ChartDataResponse(BaseModel):
    """Standard chart data response format."""

    labels: list[str]
    data: list[float]


class TimeSeriesDataset(BaseModel):
    """Dataset for time series charts."""

    label: str
    data: list[float]
    currency: str


class MultiCurrencyDataPoint(BaseModel):
    """Data point with values in all currencies."""

    ils: float
    support_usd: float
    available_usd: float
    total_usd: float
    total_ils: float


class TimeSeriesResponse(BaseModel):
    """Time series chart response format."""

    labels: list[str]
    datasets: list[TimeSeriesDataset]


class ServiceTypeExpenditureItem(BaseModel):
    """Service type expenditure breakdown item."""

    service_type_id: int
    name: str
    total_ils: float
    total_usd: float


class TimelineExpenditureItem(BaseModel):
    """Timeline expenditure item with service type breakdown."""

    time_period: str
    total_ils: float
    total_usd: float
    data: list[ServiceTypeExpenditureItem]


class TimelineExpenditureResponse(BaseModel):
    """Timeline expenditure response with service type breakdown."""

    items: list[TimelineExpenditureItem]
    group_by: Literal["day", "week", "month", "year"]


class HierarchyItem(Hierarchy):
    """Hierarchy item with detailed information."""

    count: int


class ServiceItem(Service):
    """Service item with quantity information."""

    quantity: float
    service_type_name: str


class ServiceTypeItem(ServiceType):
    """ServiceType item with count information."""

    count: int


class HierarchyDistributionResponse(BaseModel):
    """Hierarchy distribution chart with drill-down support."""

    items: list[HierarchyItem]
    level: HierarchyTypeEnum | None = None
    parent_name: str | None = None


class ServicesQuantityResponse(BaseModel):
    """Services quantity chart response."""

    data: list[ServiceItem]


class ServiceTypesDistributionResponse(BaseModel):
    """Service types distribution chart response."""

    data: list[ServiceTypeItem]


class LiveOperationFilterParams(BaseModel):
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by service type IDs",
            alias="service_type_id",
        ),
    ]


class ExpenditureTimelineRequest(FilterParams):
    """Request parameters for expenditure timeline with filters."""

    group_by: Annotated[
        Literal["day", "week", "month", "year"],
        Field(default="month", description="Time grouping: day, week, month, year"),
    ]


class HierarchyDistributionRequest(FilterParams):
    """Request parameters for hierarchy distribution with filters."""

    level: Annotated[
        HierarchyTypeEnum | None,
        Field(default=None, description="Hierarchy level to display"),
    ]
    parent_id: Annotated[
        int | None,
        Field(default=None, description="Parent hierarchy ID for drill-down"),
    ]
