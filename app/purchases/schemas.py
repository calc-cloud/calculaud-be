from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.costs.schemas import Cost
from app.stages.schemas import StageResponse


class PurchaseBase(BaseModel):
    purpose_id: int


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseUpdate(BaseModel):
    pass  # No fields to update for now


class PurchaseResponse(PurchaseBase):
    id: int
    creation_date: datetime
    costs: list[Cost]
    flow_stages: list[StageResponse | list[StageResponse]]

    model_config = ConfigDict(from_attributes=True)
