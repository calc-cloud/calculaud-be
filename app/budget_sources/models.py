from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purchases.models import Purchase


class BudgetSource(Base):
    __tablename__ = "budget_source"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Back-reference to purchases using this budget source
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase", back_populates="budget_source"
    )
