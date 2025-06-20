from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class StatusEnum(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CurrencyEnum(PyEnum):
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


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


class Purpose(Base):
    __tablename__ = "purpose"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    service_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    content: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creation_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False)
    comments: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now()
    )
    excepted_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    hierarchy_id: Mapped[int | None] = mapped_column(
        ForeignKey("hierarchy.id"), nullable=True
    )

    # Relationships
    hierarchy: Mapped["Hierarchy"] = relationship(
        "Hierarchy", back_populates="purposes"
    )
    emfs: Mapped[list["EMF"]] = relationship(
        "EMF", back_populates="purpose"
    )


class EMF(Base):
    __tablename__ = "emf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emf_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
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


class Cost(Base):
    __tablename__ = "cost"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emf_id: Mapped[int] = mapped_column(ForeignKey("emf.id"), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    emf: Mapped["EMF"] = relationship("EMF", back_populates="costs")
