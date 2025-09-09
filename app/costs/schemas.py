from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from .models import CurrencyEnum


class CostBase(BaseModel):
    currency: CurrencyEnum = Field(
        ...,
        example="SUPPORT_USD",
        description="Currency type: SUPPORT_USD, AVAILABLE_USD, or ILS",
    )
    amount: Annotated[
        float, Field(ge=0, example=50000.0, description="Cost amount (must be >= 0)")
    ]


class Cost(CostBase):
    id: int
    purchase_id: int

    model_config = ConfigDict(from_attributes=True)
