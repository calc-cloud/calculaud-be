from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app import StatusEnum
from app.emfs.schemas import EMF, EMFCreate, EMFUpdate


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
    emfs: Annotated[list[EMFCreate], Field(default_factory=list)]


class PurposeUpdate(BaseModel):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    excepted_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: Annotated[StatusEnum | None, Field(default=None)]
    supplier: Annotated[str | None, Field(default=None, max_length=200)]
    content: Annotated[str | None, Field(default=None, max_length=2000)]
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    service_type: Annotated[str | None, Field(default=None, max_length=100)]
    emfs: Annotated[list[EMFUpdate] | None, Field(default=None)]


class Purpose(PurposeBase):
    id: int
    creation_time: datetime
    last_modified: datetime
    emfs: Annotated[list[EMF], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)
