from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    service_type_id: int


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    service_type_id: Annotated[int | None, Field(default=None)]


class Service(ServiceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
