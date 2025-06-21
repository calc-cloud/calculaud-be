from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ServiceTypeBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]


class ServiceTypeCreate(ServiceTypeBase):
    pass


class ServiceTypeUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]


class ServiceType(ServiceTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
