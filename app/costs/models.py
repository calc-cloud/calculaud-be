from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer
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
