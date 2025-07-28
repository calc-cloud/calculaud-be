from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ResponsibleAuthorityBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: Annotated[str | None, Field(default=None)]


class ResponsibleAuthorityCreate(ResponsibleAuthorityBase):
    pass


class ResponsibleAuthorityUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    description: Annotated[str | None, Field(default=None)]


class ResponsibleAuthorityResponse(ResponsibleAuthorityBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
