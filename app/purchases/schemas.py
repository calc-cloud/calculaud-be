"""Pydantic schemas for purchase data validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.predefined_flows.schemas import PredefinedFlowResponse


class PurchaseBase(BaseModel):
    """Base schema for purchase."""

    purpose_id: int


class PurchaseCreate(PurchaseBase):
    """Schema for creating a purchase."""

    pass


class PurchaseResponse(PurchaseBase):
    """Schema for purchase response."""

    id: int
    predefined_flow_id: int | None
    predefined_flow: PredefinedFlowResponse | None
    creation_date: datetime

    model_config = ConfigDict(from_attributes=True)
