"""Pydantic schemas for purchase data validation."""

from datetime import datetime, timedelta
from functools import cached_property

from pydantic import BaseModel, ConfigDict, computed_field

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

    @computed_field
    @cached_property
    def current_pending_stages(self) -> list[StageResponse]:
        """Get stages in the current incomplete priority level."""
        if not self.flow_stages:
            return []

        # Find the (first) priority level with incomplete stages
        for stages in self.flow_stages:
            if isinstance(stages, list):
                # If multiple stages at this priority, check if any is incomplete
                incomplete_stages = [stage.completion_date is None for stage in stages]
                if incomplete_stages:
                    return incomplete_stages
            else:
                # Single stage at this priority
                if stages.completion_date is None:
                    return [stages]

        return []

    @computed_field
    @property
    def time_since_last_completion(self) -> timedelta | None:
        """Calculate time elapsed since the last completed stage."""
        if not self.flow_stages:
            return None

        current_pending_stages = self.current_pending_stages
        if not current_pending_stages:
            return None

        current_pending_priority = current_pending_stages[0].priority

        if current_pending_priority == 1:
            most_recent_completion_date = self.creation_date
        else:
            # Get the previous completed stages at the current pending priority
            last_completed_stages = self.flow_stages[current_pending_priority - 2]
            if isinstance(last_completed_stages, list):
                most_recent_completion_date = max(
                    stage.completion_date for stage in last_completed_stages
                )
            else:
                most_recent_completion_date = last_completed_stages.completion_date

        return datetime.now() - most_recent_completion_date

    model_config = ConfigDict(from_attributes=True)
