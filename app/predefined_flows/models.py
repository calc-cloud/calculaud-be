from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.stage_types.models import StageType


class PredefinedFlow(Base):
    __tablename__ = "predefined_flow"

    id: Mapped[int] = mapped_column(primary_key=True)
    flow_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), nullable=False
    )

    # Relationships
    predefined_flow_stages: Mapped[list["PredefinedFlowStage"]] = relationship(
        "PredefinedFlowStage",
        back_populates="predefined_flow",
        cascade="all, delete-orphan",
    )

    @property
    def flow_stages(self) -> list["PredefinedFlowStage | list[PredefinedFlowStage]"]:
        """Calculate flow stages grouped by priority."""
        if not self.predefined_flow_stages:
            return []

        stages_by_priority = {}
        for stage in self.predefined_flow_stages:
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
        return f"<PredefinedFlow(id={self.id}, name='{self.flow_name}')>"


class PredefinedFlowStage(Base):
    __tablename__ = "predefined_flow_stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    predefined_flow_id: Mapped[int] = mapped_column(
        ForeignKey("predefined_flow.id"), nullable=False
    )
    stage_type_id: Mapped[int] = mapped_column(
        ForeignKey("stage_type.id"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    predefined_flow: Mapped["PredefinedFlow"] = relationship(
        "PredefinedFlow", back_populates="predefined_flow_stages"
    )
    stage_type: Mapped["StageType"] = relationship(
        "StageType", back_populates="predefined_flow_stages"
    )

    def __repr__(self) -> str:
        return f"<PredefinedFlowStage(flow_id={self.predefined_flow_id}, priority={self.priority})>"
