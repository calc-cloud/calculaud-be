from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.hierarchies.models import HierarchyTypeEnum


class HierarchyBase(BaseModel):
    type: HierarchyTypeEnum
    name: Annotated[str, Field(min_length=1, max_length=200)]
    parent_id: Annotated[int | None, Field(default=None)]


class HierarchyCreate(HierarchyBase):
    pass


class Hierarchy(HierarchyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
