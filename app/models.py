from datetime import date, datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class StatusEnum(PyEnum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    REJECTED = "Rejected"
    COMPLETED = "Completed"


class CurrencyEnum(PyEnum):
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"


class HierarchyTypeEnum(PyEnum):
    UNIT = "unit"
    CENTER = "center"
    DEPARTMENT = "department"
    DIVISION = "division"


class Hierarchy(Base):
    __tablename__ = "hierarchy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("hierarchy.id"), nullable=True
    )
    type: Mapped[HierarchyTypeEnum] = mapped_column(
        Enum(HierarchyTypeEnum), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Self-referencing relationship
    parent: Mapped[Optional["Hierarchy"]] = relationship(
        "Hierarchy", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Hierarchy"]] = relationship(
        "Hierarchy", back_populates="parent"
    )
    # Relationship to purposes
    purposes: Mapped[List["Purpose"]] = relationship(
        "Purpose", back_populates="hierarchy"
    )


class Purpose(Base):
    __tablename__ = "purpose"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hierarchy_id: Mapped[int] = mapped_column(
        ForeignKey("hierarchy.id"), nullable=False
    )
    excepted_delivery: Mapped[date] = mapped_column(Date, nullable=False)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    comments: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False)
    creation_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    supplier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    service_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    hierarchy: Mapped["Hierarchy"] = relationship(
        "Hierarchy", back_populates="purposes"
    )
    emfs: Mapped[List["EMF"]] = relationship(
        "EMF", back_populates="purpose", cascade="all, delete-orphan"
    )


class EMF(Base):
    __tablename__ = "emf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emf_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    purpose_id: Mapped[int] = mapped_column(ForeignKey("purpose.id"), nullable=False)
    creation_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    order_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    demand_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    demand_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    bikushit_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bikushit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    purpose: Mapped["Purpose"] = relationship("Purpose", back_populates="emfs")
    costs: Mapped[List["Cost"]] = relationship(
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
