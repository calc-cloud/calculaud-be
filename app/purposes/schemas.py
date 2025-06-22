from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app import StatusEnum
from app.emfs.schemas import EMF, EMFCreate, EMFUpdate
from app.hierarchies.schemas import Hierarchy


class PurposeBase(BaseModel):
    expected_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: StatusEnum
    supplier_id: int | None = None
    content: Annotated[str | None, Field(default=None, max_length=2000)]
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    service_type_id: int | None = None


class PurposeCreate(PurposeBase):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    emfs: Annotated[list[EMFCreate], Field(default_factory=list)]


class PurposeUpdate(BaseModel):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    expected_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: Annotated[StatusEnum | None, Field(default=None)]
    supplier_id: int | None = None
    service_type_id: int | None = None
    content: Annotated[str | None, Field(default=None, max_length=2000)]
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    emfs: Annotated[list[EMFUpdate] | None, Field(default=None)]


class Purpose(PurposeBase):
    id: int
    creation_time: datetime
    last_modified: datetime

    supplier: str | None = None
    service_type: str | None = None
    hierarchy: Hierarchy | None = None

    emfs: Annotated[list[EMF], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)
