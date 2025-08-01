from datetime import date
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
    completion_date: Annotated[date | None, Field(default=None)]


class StageCompletion(BaseModel):
    value: Annotated[str | None, Field(default=None)]


class StageResponse(StageBase):
    id: int
    purchase_id: int
    stage_type: StageTypeResponse  # full stage type object relationship
    completion_date: date | None
    days_since_previous_stage: int | None = None

    model_config = ConfigDict(from_attributes=True)
