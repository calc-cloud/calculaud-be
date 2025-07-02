from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.stage_types.schemas import StageTypeResponse


class StageBase(BaseModel):
    stage_type_id: int
    priority: Annotated[int, Field(ge=1)]
    value: Annotated[str | None, Field(default=None)]


class StageCreate(StageBase):
    pass


class StageUpdate(BaseModel):
    value: Annotated[str | None, Field(default=None)]


class StageCompletion(BaseModel):
    value: Annotated[str | None, Field(default=None)]


class StageResponse(StageBase):
    id: int
    purchase_id: int
    stage_type: StageTypeResponse  # full stage type object relationship
    completion_date: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
