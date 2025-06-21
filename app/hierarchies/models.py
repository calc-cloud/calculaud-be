from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purposes.models import Purpose


class HierarchyTypeEnum(PyEnum):
    UNIT = "UNIT"
    CENTER = "CENTER"
    ANAF = "ANAF"
    TEAM = "TEAM"


class Hierarchy(Base):
    __tablename__ = "hierarchy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("hierarchy.id"), nullable=True
    )
    type: Mapped[HierarchyTypeEnum] = mapped_column(
        Enum(HierarchyTypeEnum), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False, default="")

    # Self-referencing relationship
    parent: Mapped["Hierarchy"] = relationship(
        "Hierarchy", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Hierarchy"]] = relationship(
        "Hierarchy", back_populates="parent"
    )
    # Relationship to purposes
    purposes: Mapped[list["Purpose"]] = relationship(
        "Purpose", back_populates="hierarchy"
    )
