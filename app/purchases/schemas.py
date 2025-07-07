"""Pydantic schemas for purchase data validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.costs.schemas import Cost, CostBase
from app.stages.schemas import StageResponse


class PurchaseBase(BaseModel):
    """Base schema for purchase."""

    purpose_id: int


class PurchaseCreate(PurchaseBase):
    """Schema for creating a purchase."""

    costs: list[CostBase] = []


class PurchaseResponse(PurchaseBase):
    """Schema for purchase response."""

    id: int
    creation_date: datetime
    costs: list[Cost] = []
    flow_stages: list[StageResponse | list[StageResponse]] = []

    model_config = ConfigDict(from_attributes=True)
