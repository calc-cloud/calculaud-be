from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purposes.models import Purpose


class HierarchyTypeEnum(PyEnum):
    """
    Organizational hierarchy levels in descending order of authority.

    Business Hierarchy (Top to Bottom):
    UNIT (highest) → CENTER → ANAF → MADOR → TEAM (lowest)

    Validation Rules:
    - Child entities can only be assigned to parents of higher hierarchy level
    - Procurement purposes inherit permissions from their hierarchy level
    - Approval workflows follow hierarchy chain upward for authorization

    IMPORTANT: Enum order matters for validation logic - DO NOT reorder!
    """

    UNIT = "UNIT"  # Top-level organizational unit (highest authority)
    CENTER = "CENTER"  # Major operational center within unit
    ANAF = "ANAF"  # Branch/division within center
    MADOR = "MADOR"  # Department within branch
    TEAM = "TEAM"  # Working team within department (lowest level)


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
    path: Mapped[str] = mapped_column(
        String(1000), nullable=False, default="", index=True
    )

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
