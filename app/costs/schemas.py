from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from .models import CurrencyEnum


class CostBase(BaseModel):
    currency: CurrencyEnum
    amount: Annotated[float, Field(ge=0)]


class Cost(CostBase):
    id: int
    purchase_id: int

    model_config = ConfigDict(from_attributes=True)
