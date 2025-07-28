from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class StageTypeBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    display_name: Annotated[str, Field(min_length=1, max_length=255)]
    description: Annotated[str | None, Field(default=None)]
    value_required: Annotated[bool, Field(default=False)]
    responsible_authority: Annotated[str | None, Field(default=None, max_length=255)]


class StageTypeCreate(StageTypeBase):
    pass


class StageTypeUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    display_name: Annotated[
        str | None, Field(default=None, min_length=1, max_length=255)
    ]
    description: Annotated[str | None, Field(default=None)]
    value_required: Annotated[bool | None, Field(default=None)]
    responsible_authority: Annotated[str | None, Field(default=None, max_length=255)]


class StageTypeResponse(StageTypeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
