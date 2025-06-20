from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..costs.schemas import Cost


class EMFBase(BaseModel):
    emf_id: Annotated[str, Field(min_length=1, max_length=255)]
    order_id: Annotated[str | None, Field(default=None, max_length=255)]
    order_creation_date: Annotated[date | None, Field(default=None)]
    demand_id: Annotated[str | None, Field(default=None, max_length=255)]
    demand_creation_date: Annotated[date | None, Field(default=None)]
    bikushit_id: Annotated[str | None, Field(default=None, max_length=255)]
    bikushit_creation_date: Annotated[date | None, Field(default=None)]


class EMFCreate(EMFBase):
    pass


class EMF(EMFBase):
    id: int
    purpose_id: int
    creation_time: datetime
    costs: Annotated[list[Cost], Field(default_factory=list)]

    model_config = ConfigDict(from_attributes=True)
