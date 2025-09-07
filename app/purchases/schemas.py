"""Pydantic schemas for purchase data validation."""

from datetime import date, datetime
from functools import cached_property

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.budget_sources.schemas import BudgetSource
from app.costs.schemas import Cost, CostBase
from app.responsible_authorities.schemas import ResponsibleAuthorityResponse
from app.stages.schemas import StageResponse


class PurchaseBase(BaseModel):
    """Base schema for purchase."""

    purpose_id: int = Field(
        ..., example=1, description="ID of the purpose this purchase belongs to"
    )
    budget_source_id: int | None = Field(
        None, example=2, description="Optional ID of the budget source"
    )


class PurchaseCreate(PurchaseBase):
    """Schema for creating a purchase."""

    costs: list[CostBase] = Field(
        default_factory=list,
        example=[
            {"currency": "SUPPORT_USD", "amount": 50000.0},
            {"currency": "ILS", "amount": 25000.0},
        ],
        description="Optional list of costs for this purchase",
    )


class PurchaseUpdate(BaseModel):
    """Schema for updating a purchase (partial update)."""

    budget_source_id: int | None = Field(
        default=None, example=3, description="Optional ID of the budget source"
    )


class PurchaseResponse(PurchaseBase):
    """Schema for purchase response."""

    id: int
    creation_date: datetime
    costs: list[Cost] = []
    budget_source: BudgetSource | None = None
    pending_authority: ResponsibleAuthorityResponse | None = None
    flow_stages: list[StageResponse | list[StageResponse]] = []

    @field_validator("flow_stages", mode="after")
    def calculate_days_since_previous_stage(
        cls, flow_stages: list[StageResponse | list[StageResponse]], info
    ) -> list[StageResponse | list[StageResponse]]:
        """Calculate days_since_previous_stage for each stage."""
        if not flow_stages or not info.data:
            return flow_stages

        # Process each priority level
        current_date = datetime.now().date()
        for stages in flow_stages:
            if isinstance(stages, list):
                # Multiple stages at this priority
                for stage in stages:
                    target_date = stage.completion_date or current_date
                    days_since_previous = cls._get_days_since_reference(
                        stage.priority, flow_stages, target_date
                    )
                    stage.days_since_previous_stage = days_since_previous
            else:
                # Single stage at this priority
                target_date = stages.completion_date or current_date
                days_since_previous = cls._get_days_since_reference(
                    stages.priority, flow_stages, target_date
                )
                stages.days_since_previous_stage = days_since_previous

        return flow_stages

    @classmethod
    def _get_days_since_reference(
        cls,
        priority: int,
        all_flow_stages: list,
        target_date: date | None = None,
    ) -> int | None:
        """
        Unified helper method to calculate days since reference date.

        Args:
            priority: Priority level to calculate for
            all_flow_stages: All flow stages for reference lookup
            target_date: Target date to calculate to (defaults to current date)

        Returns:
            Days elapsed from reference to target date, or None if no reference found
        """
        if target_date is None:
            target_date = datetime.now().date()

        # For priority 1 stages, always return None
        if priority == 1:
            return None
        else:
            # Find the most recent completion date from previous priority level
            previous_priority = priority - 1
            reference_date = None

            # Look through all_flow_stages to find previous priority stages
            for stages in all_flow_stages:
                if isinstance(stages, list):
                    # Multiple stages at this priority
                    if stages and stages[0].priority == previous_priority:
                        completed_stages = [
                            s for s in stages if s.completion_date is not None
                        ]
                        if completed_stages:
                            reference_date = max(
                                s.completion_date for s in completed_stages
                            )
                        break
                else:
                    # Single stage at this priority
                    if (
                        stages.priority == previous_priority
                        and stages.completion_date is not None
                    ):
                        reference_date = stages.completion_date
                        break

            if reference_date is None:
                return None

        return (target_date - reference_date).days

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
                incomplete_stages = [
                    stage for stage in stages if stage.completion_date is None
                ]
                if incomplete_stages:
                    return incomplete_stages
            else:
                # Single stage at this priority
                if stages.completion_date is None:
                    return [stages]

        return []

    @computed_field
    @property
    def days_since_last_completion(self) -> int | None:
        """Calculate days elapsed since the last completed stage."""
        if not self.flow_stages:
            return None

        current_pending_stages = self.current_pending_stages
        if not current_pending_stages:
            return None

        current_pending_priority = current_pending_stages[0].priority

        # Use the unified method to calculate days since reference
        return self._get_days_since_reference(
            current_pending_priority, self.flow_stages
        )

    model_config = ConfigDict(from_attributes=True)
