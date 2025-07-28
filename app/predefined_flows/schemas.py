from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.stage_types.schemas import StageTypeResponse


class PredefinedFlowStageResponse(BaseModel):
    id: int
    predefined_flow_id: int
    stage_type_id: int
    stage_type: StageTypeResponse  # full stage type object relationship
    priority: int

    model_config = ConfigDict(from_attributes=True)


class PredefinedFlowBase(BaseModel):
    flow_name: Annotated[str, Field(max_length=255)]


class PredefinedFlowCreate(PredefinedFlowBase):
    stages: list[
        int | str | list[int | str]
    ]  # List of stage_type_ids/names or lists of stage_type_ids/names for same priority


class PredefinedFlowUpdate(BaseModel):
    flow_name: Annotated[str | None, Field(default=None, max_length=255)]
    stages: list[int | str | list[int | str]] | None = (
        None  # List of stage_type_ids/names or lists for same priority
    )


class PredefinedFlowResponse(PredefinedFlowBase):
    id: int
    created_at: datetime
    flow_stages: list[PredefinedFlowStageResponse | list[PredefinedFlowStageResponse]]

    model_config = ConfigDict(from_attributes=True)


class PredefinedFlowEditResponse(PredefinedFlowBase):
    id: int
    created_at: datetime
    stages: list[str | list[str]]  # Simplified format with stage names for editing

    model_config = ConfigDict(from_attributes=True)
