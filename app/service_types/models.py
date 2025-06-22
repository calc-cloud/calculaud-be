from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app import Service


class ServiceType(Base):
    __tablename__ = "service_type"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Relationships
    services: Mapped[list["Service"]] = relationship(
        back_populates="service_type", cascade="all, delete-orphan"
    )
