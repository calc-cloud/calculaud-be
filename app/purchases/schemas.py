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

        last_completed_priority = None
        most_recent_completion = self.current_pending_stages(π)

        # Find the most recent completion date from the last completed priority
        for stages in self.flow_stages:
            if isinstance(stages, list):
                # If multiple stages at this priority, check each one
                for stage in stages:
                    if stage.completion_date is not None:
                        if (
                            most_recent_completion is None
                            or stage.completion_date > most_recent_completion
                        ):
                            most_recent_completion = stage.completion_date
            else:
                # Single stage at this priority
                if stages.completion_date is not None:
                    if (
                        most_recent_completion is None
                        or stages.completion_date > most_recent_completion
                    ):
                        most_recent_completion = stages.completion_date

        if most_recent_completion is None:
            return None

        return datetime.now() - most_recent_completion


    model_config = ConfigDict(from_attributes=True)
