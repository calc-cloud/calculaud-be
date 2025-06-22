from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purposes.models import Purpose


class HierarchyTypeEnum(PyEnum):
    # IMPORTANT: The order of these enum values matters for hierarchy validation
    # Higher level types should come first, lower level types should come after
    # Valid hierarchy: UNIT -> CENTER -> ANAF -> MADOR -> TEAM
    # A child type can only be assigned to a parent of a higher hierarchy level (not equal)
    UNIT = "UNIT"
    CENTER = "CENTER"
    ANAF = "ANAF"
    MADOR = "MADOR"
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
    path: Mapped[str] = mapped_column(String(1000), nullable=False, default="", index=True)

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
