from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app import ServiceType


class Service(Base):
    __tablename__ = "service"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service_type_id: Mapped[int] = mapped_column(
        ForeignKey("service_type.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    service_type: Mapped["ServiceType"] = relationship(back_populates="services")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "name", "service_type_id", name="uq_service_name_service_type"
        ),
    )
