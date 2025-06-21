from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]


class Supplier(SupplierBase):
    id: int

    model_config = ConfigDict(from_attributes=True) 