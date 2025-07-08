from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purchases.models import Purchase
    from app.stage_types.models import StageType


class Stage(Base):
    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_type_id: Mapped[int] = mapped_column(
        ForeignKey("stage_type.id"), nullable=False
    )
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchase.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    stage_type: Mapped["StageType"] = relationship("StageType", back_populates="stages")
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="stages")

    def __repr__(self) -> str:
        return f"<Stage(id={self.id}, priority={self.priority}, completed={self.completion_date is not None})>"
