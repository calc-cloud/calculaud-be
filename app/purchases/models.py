from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, event, func
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.budget_sources.models import BudgetSource
    from app.costs.models import Cost
    from app.predefined_flows.models import PredefinedFlow
    from app.purposes.models import Purpose
    from app.responsible_authorities.models import ResponsibleAuthority
    from app.stages.models import Stage


class Purchase(Base):
    __tablename__ = "purchase"

    id: Mapped[int] = mapped_column(primary_key=True)
    purpose_id: Mapped[int] = mapped_column(
        ForeignKey("purpose.id"), nullable=False, index=True
    )
    predefined_flow_id: Mapped[int | None] = mapped_column(
        ForeignKey("predefined_flow.id"), nullable=True
    )
    budget_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("budget_source.id"), nullable=True, index=True
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), nullable=False
    )

    # Relationships
    purpose: Mapped["Purpose"] = relationship("Purpose", back_populates="purchases")
    predefined_flow: Mapped["PredefinedFlow"] = relationship(
        "PredefinedFlow", back_populates="purchases"
    )
    budget_source: Mapped["BudgetSource | None"] = relationship(
        "BudgetSource", back_populates="purchases"
    )
    stages: Mapped[list["Stage"]] = relationship(
        "Stage", back_populates="purchase", cascade="all, delete-orphan"
    )
    costs: Mapped[list["Cost"]] = relationship(
        "Cost", back_populates="purchase", cascade="all, delete-orphan"
    )

    @property
    def pending_authority(self) -> "ResponsibleAuthority | None":
        """
        Return the responsible authority for the highest priority incomplete stage.

        This property uses the same SQL logic as the filtering functions to ensure
        consistency. It prioritizes incomplete stages first, then sorts by priority
        ascending, with deterministic tie-breaking by stage_type.id.

        NOTE: Must use the same logic as get_pending_authority_query() in
        app.purposes.pending_authority_utils to maintain consistency.
        """
        from app.purposes.pending_authority_utils import get_pending_authority_object

        # Get the session from the object to execute the query
        session = object_session(self)
        if not session:
            return None

        return get_pending_authority_object(
            session, purchase_id=self.id, purpose_id=self.purpose_id
        )

    @property
    def flow_stages(self) -> list["Stage | list[Stage]"]:
        """Calculate flow stages grouped by priority."""
        if not self.stages:
            return []

        stages_by_priority = {}
        for stage in self.stages:
            if stage.priority not in stages_by_priority:
                stages_by_priority[stage.priority] = []
            stages_by_priority[stage.priority].append(stage)

        result = []
        for priority in sorted(stages_by_priority.keys()):
            priority_stages = stages_by_priority[priority]
            if len(priority_stages) == 1:
                result.append(priority_stages[0])
            else:
                result.append(priority_stages)

        return result

    def __repr__(self) -> str:
        return f"<Purchase(id={self.id}, purpose_id={self.purpose_id}, stages={len(self.stages)})>"


# Event listeners for Purchase
@event.listens_for(Purchase, "after_insert")
@event.listens_for(Purchase, "after_update")
@event.listens_for(Purchase, "after_delete")
def _update_purpose_on_purchase_change(_mapper, connection, target: Purchase) -> None:
    """Update Purpose.last_modified when Purchase changes."""
    if hasattr(target, "purpose_id") and target.purpose_id:
        from app.purposes.models import update_purpose_last_modified

        update_purpose_last_modified(connection, target.purpose_id)
