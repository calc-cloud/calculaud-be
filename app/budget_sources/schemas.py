from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BudgetSourceBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]


class BudgetSourceCreate(BudgetSourceBase):
    pass


class BudgetSourceUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]


class BudgetSource(BudgetSourceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
