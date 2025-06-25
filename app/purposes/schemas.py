from datetime import date, datetime
from typing import Annotated, Literal

from fastapi.params import Query
from pydantic import BaseModel, ConfigDict, Field

from app import StatusEnum
from app.emfs.schemas import EMF, EMFCreate, EMFUpdate
from app.files.schemas import FileAttachment
from app.hierarchies.schemas import Hierarchy
from app.pagination import PaginationParams


class PurposeContentBase(BaseModel):
    service_id: int
    quantity: Annotated[int, Field(ge=1)]


class PurposeContentCreate(PurposeContentBase):
    pass


class PurposeContentUpdate(PurposeContentBase):
    pass


class PurposeContent(PurposeContentBase):
    id: int
    service_name: str
    service_type: str

    model_config = ConfigDict(from_attributes=True)


class PurposeBase(BaseModel):
    expected_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: Annotated[StatusEnum, Field(default=StatusEnum.IN_PROGRESS)]
    supplier_id: int | None = None
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    service_type_id: int | None = None


class PurposeCreate(PurposeBase):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    emfs: Annotated[list[EMFCreate], Field(default_factory=list)]
    file_attachment_ids: Annotated[list[int], Field(default_factory=list)]
    contents: Annotated[list[PurposeContentCreate], Field(default_factory=list)]


class PurposeUpdate(BaseModel):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    expected_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: Annotated[StatusEnum | None, Field(default=None)]
    supplier_id: int | None = None
    service_type_id: int | None = None
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    emfs: Annotated[list[EMFUpdate] | None, Field(default=None)]
    file_attachment_ids: Annotated[list[int] | None, Field(default=None)]
    contents: Annotated[list[PurposeContentUpdate] | None, Field(default=None)]


class Purpose(PurposeBase):
    id: int
    creation_time: datetime
    last_modified: datetime

    supplier: str | None = None
    service_type: str | None = None
    hierarchy: Hierarchy | None = None

    emfs: Annotated[list[EMF], Field(default_factory=list)]
    file_attachments: Annotated[list[FileAttachment], Field(default_factory=list)]
    contents: Annotated[list[PurposeContent], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)


class FilterParams(BaseModel):
    """Universal filter parameters for analytics endpoints."""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    start_date: Annotated[
        date | None,
        Query(default=None, description="Filter by purpose creation date from"),
    ]
    end_date: Annotated[
        date | None,
        Query(default=None, description="Filter by purpose creation date to"),
    ]
    service_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by specific service IDs",
            alias="service_id",
        ),
    ]
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by service type IDs",
            alias="service_type_id",
        ),
    ]
    hierarchy_ids: Annotated[
        list[int] | None,
        Query(
            default=None, description="Filter by hierarchy IDs", alias="hierarchy_id"
        ),
    ]
    statuses: Annotated[
        list[StatusEnum] | None,
        Query(default=None, description="Filter by purpose status", alias="status"),
    ]
    supplier_ids: Annotated[
        list[int] | None,
        Query(default=None, description="Filter by supplier IDs", alias="supplier_id"),
    ]


class GetPurposesRequest(FilterParams, PaginationParams):
    """Request parameters for getting purposes with filters."""

    search: Annotated[
        str | None,
        Field(default=None, description="Search in description and EMF IDs..."),
    ]
    sort_by: Annotated[
        str,
        Field(default="creation_time", description="Sort by field"),
    ]
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(default="desc", description="Sort order: asc or desc"),
    ]
