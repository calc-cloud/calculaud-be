from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.emfs.models import EMF


class CurrencyEnum(PyEnum):
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


class Cost(Base):
    __tablename__ = "cost"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emf_id: Mapped[int] = mapped_column(ForeignKey("emf.id"), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    emf: Mapped["EMF"] = relationship("EMF", back_populates="costs")
