from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.predefined_flows.models import PredefinedFlowStage
    from app.responsible_authorities.models import ResponsibleAuthority
    from app.stages.models import Stage


class StageType(Base):
    __tablename__ = "stage_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    responsible_authority_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("responsible_authority.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now(), nullable=False
    )

    # Relationships
    responsible_authority: Mapped["ResponsibleAuthority | None"] = relationship(
        "ResponsibleAuthority", back_populates="stage_types", lazy="joined"
    )
    stages: Mapped[list["Stage"]] = relationship("Stage", back_populates="stage_type")
    predefined_flow_stages: Mapped[list["PredefinedFlowStage"]] = relationship(
        "PredefinedFlowStage", back_populates="stage_type"
    )
