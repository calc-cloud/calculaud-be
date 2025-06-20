from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app import StatusEnum
from app.emfs.schemas import EMF


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


class PaginatedResponse(BaseModel):
    items: list[Purpose]
    total: Annotated[int, Field(ge=0)]
    page: Annotated[int, Field(ge=1)]
    limit: Annotated[int, Field(ge=1, le=100)]
