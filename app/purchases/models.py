from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.costs.models import Cost
    from app.purposes.models import Purpose
    from app.stages.models import Stage


class Purchase(Base):
    __tablename__ = "purchase"

    id: Mapped[int] = mapped_column(primary_key=True)
    purpose_id: Mapped[int] = mapped_column(ForeignKey("purpose.id"), nullable=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False
    )

    # Relationships
    purpose: Mapped["Purpose"] = relationship("Purpose", back_populates="purchases")
    stages: Mapped[list["Stage"]] = relationship(
        "Stage", back_populates="purchase", cascade="all, delete-orphan"
    )
    costs: Mapped[list["Cost"]] = relationship(
        "Cost", back_populates="purchase", cascade="all, delete-orphan"
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
