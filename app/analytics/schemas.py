from datetime import date
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.purposes.models import StatusEnum
from app.service_types.schemas import ServiceType

# Generic type for distribution response data
T = TypeVar("T")


class DistributionResponse(BaseModel, Generic[T]):
    """Generic distribution chart response."""

    data: list[T]


class CurrencyAmounts(BaseModel):
    """Input currency amounts for multi-currency calculations."""

    ils: float = 0.0
    support_usd: float = 0.0
    available_usd: float = 0.0


class MultiCurrencyAmount(BaseModel):
    """Amount values in multiple currencies."""

    ils: float
    support_usd: float
    available_usd: float
    total_usd: float
    total_ils: float


class ServiceBreakdownItem(BaseModel):
    """Service breakdown for stacked charts."""

    service_id: int
    service_name: str
    quantity: int


class ServiceTypeItem(ServiceType):
    """ServiceType item with count information."""

    count: int


class StatusItem(BaseModel):
    """Status item with count information."""

    status: str
    count: int


class PendingAuthorityItem(BaseModel):
    """Pending authority item with count information."""

    authority_id: int | None
    authority_name: str | None
    count: int


class PendingStageItem(BaseModel):
    """Pending stage item with count information."""

    stage_type_id: int | None
    stage_type_name: str | None
    count: int


class ServiceTypeBreakdownItem(BaseModel):
    """Service type breakdown for stacked charts."""

    service_type_id: int
    service_type_name: str
    count: int


class PendingStageWithBreakdownItem(BaseModel):
    """Pending stage with service type breakdown for stacked bar charts."""

    stage_type_id: int | None
    stage_type_name: str | None
    total_count: int
    service_types: list[ServiceTypeBreakdownItem]


class ServiceTypeWithBreakdownItem(BaseModel):
    """Service type with service breakdown for stacked bar charts."""

    service_type_id: int
    service_type_name: str
    total_quantity: int
    services: list[ServiceBreakdownItem]


class ServicesQuantityStackedResponse(BaseModel):
    """Services quantity stacked chart response."""

    data: list[ServiceTypeWithBreakdownItem]


class PurposeProcessingTimeByServiceType(BaseModel):
    """Purpose processing time analytics for a specific service type."""

    service_type_id: int | None
    service_type_name: str
    count: int
    average_processing_days: float
    min_processing_days: int
    max_processing_days: int


class PurposeProcessingTimeDistributionResponse(BaseModel):
    """Dashboard response for purpose processing time distribution by service type."""

    service_types: list[PurposeProcessingTimeByServiceType]
    total_purposes: int


class AnalyticsFilterParams(BaseModel):
    """Simple filter parameters for analytics endpoints."""

    start_date: Annotated[
        date | None,
        Query(default=None, description="Start date for filtering"),
    ]
    end_date: Annotated[
        date | None,
        Query(default=None, description="End date for filtering"),
    ]
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by service type IDs",
            alias="service_type_id",
        ),
    ]


class LiveOperationFilterParams(BaseModel):
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by service type IDs",
            alias="service_type_id",
        ),
    ]


class ServiceTypeStatusDistributionResponse(BaseModel):
    """Service type distribution for purposes that changed to a specific status."""

    data: list[ServiceTypeBreakdownItem]
    total_count: int
    target_status: StatusEnum


class ServiceTypeCostItem(BaseModel):
    """Service type with cost amounts in multiple currencies."""

    service_type_id: int | None
    service_type_name: str
    amounts: MultiCurrencyAmount


class BudgetSourceCostItem(BaseModel):
    """Budget source with cost amounts in multiple currencies."""

    budget_source_id: int | None
    budget_source_name: str
    amounts: MultiCurrencyAmount


# Type aliases for specific distribution responses using generic base
ServiceTypesDistributionResponse = DistributionResponse[ServiceTypeItem]
StatusesDistributionResponse = DistributionResponse[StatusItem]
PendingAuthoritiesDistributionResponse = DistributionResponse[PendingAuthorityItem]
PendingStagesDistributionResponse = DistributionResponse[PendingStageItem]
PendingStagesStackedDistributionResponse = DistributionResponse[
    PendingStageWithBreakdownItem
]
ServiceTypeCostDistributionResponse = DistributionResponse[ServiceTypeCostItem]
BudgetSourceCostDistributionResponse = DistributionResponse[BudgetSourceCostItem]
