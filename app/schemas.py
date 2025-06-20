from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class StatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CurrencyEnum(str, Enum):
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


class HierarchyTypeEnum(str, Enum):
    UNIT = "UNIT"
    CENTER = "CENTER"
    ANAF = "ANAF"
    TEAM = "TEAM"


# Hierarchy schemas
class HierarchyBase(BaseModel):
    type: HierarchyTypeEnum
    name: Annotated[str, Field(min_length=1, max_length=200)]
    parent_id: Annotated[int | None, Field(default=None)]


class HierarchyCreate(HierarchyBase):
    pass


class Hierarchy(HierarchyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Cost schemas
class CostBase(BaseModel):
    currency: CurrencyEnum
    cost: Annotated[float, Field(ge=0)]


class CostCreate(CostBase):
    pass


class Cost(CostBase):
    id: int
    emf_id: int

    model_config = ConfigDict(from_attributes=True)


# EMF schemas
class EMFBase(BaseModel):
    emf_id: Annotated[str, Field(min_length=1, max_length=255)]
    order_id: Annotated[str | None, Field(default=None, max_length=255)]
    order_creation_date: Annotated[date | None, Field(default=None)]
    demand_id: Annotated[str | None, Field(default=None, max_length=255)]
    demand_creation_date: Annotated[date | None, Field(default=None)]
    bikushit_id: Annotated[str | None, Field(default=None, max_length=255)]
    bikushit_creation_date: Annotated[date | None, Field(default=None)]


class EMFCreate(EMFBase):
    pass


class EMF(EMFBase):
    id: int
    purpose_id: int
    creation_time: datetime
    costs: Annotated[list[Cost], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)


# Purpose schemas
class PurposeBase(BaseModel):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    excepted_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: StatusEnum
    supplier: Annotated[str | None, Field(default=None, max_length=200)]
    content: Annotated[str | None, Field(default=None, max_length=2000)]
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    service_type: Annotated[str | None, Field(default=None, max_length=100)]


class PurposeCreate(PurposeBase):
    pass


class Purpose(PurposeBase):
    id: int
    creation_time: datetime
    last_modified: datetime
    emfs: Annotated[list[EMF], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)


# Response schemas
class PaginatedResponse(BaseModel):
    items: list[Purpose]
    total: Annotated[int, Field(ge=0)]
    page: Annotated[int, Field(ge=1)]
    limit: Annotated[int, Field(ge=1, le=100)]
