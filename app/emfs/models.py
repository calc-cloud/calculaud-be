from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.costs.models import Cost
    from app.purposes.models import Purpose


class EMF(Base):
    __tablename__ = "emf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emf_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose_id: Mapped[int] = mapped_column(ForeignKey("purpose.id"), nullable=False)
    creation_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    demand_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    demand_creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    bikushit_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bikushit_creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    purpose: Mapped["Purpose"] = relationship("Purpose", back_populates="emfs")
    costs: Mapped[list["Cost"]] = relationship(
        "Cost", back_populates="emf", cascade="all, delete-orphan"
    )
