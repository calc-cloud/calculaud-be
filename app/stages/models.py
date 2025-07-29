from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Text, event, text
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
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchase.id"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    stage_type: Mapped["StageType"] = relationship("StageType", back_populates="stages")
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="stages")

    def __repr__(self) -> str:
        return f"<Stage(id={self.id}, priority={self.priority}, completed={self.completion_date is not None})>"


# Event listeners for Stage
@event.listens_for(Stage, "after_insert")
@event.listens_for(Stage, "after_update")
@event.listens_for(Stage, "after_delete")
def _update_purpose_on_stage_change(_mapper, connection, target: Stage) -> None:
    """Update Purpose.last_modified when Stage changes."""
    if hasattr(target, "purchase_id") and target.purchase_id:
        # Query for purpose_id through purchase
        result = connection.execute(
            text("SELECT purpose_id FROM purchase WHERE id = :purchase_id"),
            {"purchase_id": target.purchase_id},
        ).fetchone()
        if result and result[0]:
            from app.purposes.models import update_purpose_last_modified

            update_purpose_last_modified(connection, result[0])
