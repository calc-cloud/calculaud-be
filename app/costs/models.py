from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer, event, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app import Purchase


class CurrencyEnum(PyEnum):
    SUPPORT_USD = "SUPPORT_USD"
    AVAILABLE_USD = "AVAILABLE_USD"
    ILS = "ILS"


class Cost(Base):
    __tablename__ = "cost"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchase.id"), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="costs")


# Event listeners for Cost
@event.listens_for(Cost, "after_insert")
@event.listens_for(Cost, "after_update")
@event.listens_for(Cost, "after_delete")
def _update_purpose_on_cost_change(_mapper, connection, target: Cost) -> None:
    """Update Purpose.last_modified when Cost changes."""
    if hasattr(target, "purchase_id") and target.purchase_id:
        # Query for purpose_id through purchase
        result = connection.execute(
            text("SELECT purpose_id FROM purchase WHERE id = :purchase_id"),
            {"purchase_id": target.purchase_id},
        ).fetchone()
        if result and result[0]:
            from app.purposes.models import update_purpose_last_modified

            update_purpose_last_modified(connection, result[0])
