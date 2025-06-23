from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field

from app.costs.models import CurrencyEnum
from app.hierarchies.models import HierarchyTypeEnum
from app.hierarchies.schemas import Hierarchy
from app.purposes.models import StatusEnum


class FilterParams(BaseModel):
    """Universal filter parameters for analytics endpoints."""

    start_date: Annotated[
        date | None,
        Field(default=None, description="Filter by purpose creation date from"),
    ]
    end_date: Annotated[
        date | None,
        Field(default=None, description="Filter by purpose creation date to"),
    ]
    service_ids: Annotated[
        list[int] | None,
        Field(default=None, description="Filter by specific service IDs"),
    ]
    service_type_ids: Annotated[
        list[int] | None, Field(default=None, description="Filter by service type IDs")
    ]
    hierarchy_ids: Annotated[
        list[int] | None, Field(default=None, description="Filter by hierarchy IDs")
    ]
    status: Annotated[
        list[StatusEnum] | None,
        Field(default=None, description="Filter by purpose status"),
    ]
    supplier_ids: Annotated[
        list[int] | None, Field(default=None, description="Filter by supplier IDs")
    ]


class ChartDataResponse(BaseModel):
    """Standard chart data response format."""

    labels: list[str]
    data: list[float]


class TimeSeriesDataset(BaseModel):
    """Dataset for time series charts."""

    label: str
    data: list[float]
    currency: str


class TimeSeriesResponse(BaseModel):
    """Time series chart response format."""

    labels: list[str]
    datasets: list[TimeSeriesDataset]


class HierarchyItem(Hierarchy):
    """Hierarchy item with detailed information."""

    count: int


class HierarchyDistributionResponse(BaseModel):
    """Hierarchy distribution chart with drill-down support."""

    items: list[HierarchyItem]
    level: HierarchyTypeEnum | None = None
    parent_name: str | None = None


class ServicesQuantityResponse(ChartDataResponse):
    """Services quantity chart response."""

    pass


class ServiceTypesDistributionResponse(ChartDataResponse):
    """Service types distribution chart response."""

    data: list[int]  # Override to use int for counts


class ExpenditureTimelineRequest(FilterParams):
    """Request parameters for expenditure timeline with filters."""

    currency: Annotated[
        CurrencyEnum, Field(description="Currency to display (ILS/USD)")
    ]
    group_by: Annotated[
        str, Field(default="month", description="Time grouping: day, week, month, year")
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
