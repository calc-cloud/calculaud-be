from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.hierarchies.models import HierarchyTypeEnum


class HierarchyBase(BaseModel):
    type: HierarchyTypeEnum
    name: Annotated[str, Field(min_length=1, max_length=200)]
    parent_id: Annotated[int | None, Field(default=None)]


class HierarchyCreate(HierarchyBase):
    pass


class HierarchyUpdate(BaseModel):
    type: Annotated[HierarchyTypeEnum | None, Field(default=None)]
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=200)]
    parent_id: Annotated[int | None, Field(default=None)]


class Hierarchy(HierarchyBase):
    id: int
    path: str

    model_config = ConfigDict(from_attributes=True)


class HierarchyWithChildren(Hierarchy):
    children: Annotated[list["HierarchyWithChildren"], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)


class HierarchyTree(BaseModel):
    id: int
    type: HierarchyTypeEnum
    name: str
    parent_id: Annotated[int | None, Field(default=None)]
    path: str
    children: Annotated[list["HierarchyTree"], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)
