from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.responsible_authorities.schemas import ResponsibleAuthorityResponse


class StageTypeBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    display_name: Annotated[str, Field(min_length=1, max_length=255)]
    description: Annotated[str | None, Field(default=None)]
    value_required: Annotated[bool, Field(default=False)]
    responsible_authority_id: Annotated[int | None, Field(default=None)]


class StageTypeCreate(StageTypeBase):
    pass


class StageTypeUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    display_name: Annotated[
        str | None, Field(default=None, min_length=1, max_length=255)
    ]
    description: Annotated[str | None, Field(default=None)]
    value_required: Annotated[bool | None, Field(default=None)]
    responsible_authority_id: Annotated[int | None, Field(default=None)]


class StageTypeResponse(StageTypeBase):
    id: int
    created_at: datetime
    responsible_authority: ResponsibleAuthorityResponse | None = None

    model_config = ConfigDict(from_attributes=True)
