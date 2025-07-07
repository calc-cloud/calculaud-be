from datetime import UTC, date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.files.models import FileAttachment
    from app.hierarchies.models import Hierarchy
    from app.purchases.models import Purchase
    from app.service_types.models import ServiceType
    from app.services.models import Service
    from app.suppliers.models import Supplier


class StatusEnum(PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Purpose(Base):
    __tablename__ = "purpose"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    description: Mapped[str | None] = mapped_column(
        String(2000), nullable=True, index=True
    )
    creation_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum), nullable=False, index=True
    )
    comments: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime,
        onupdate=datetime.now(UTC),
        server_default=func.now(),
        server_onupdate=func.now(),
    )
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    hierarchy_id: Mapped[int | None] = mapped_column(
        ForeignKey("hierarchy.id"), nullable=True, index=True
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier.id"), nullable=True, index=True
    )
    service_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_type.id"), nullable=True, index=True
    )

    # Relationships
    hierarchy: Mapped["Hierarchy"] = relationship(
        "Hierarchy", back_populates="purposes", lazy="joined"
    )
    _supplier: Mapped["Supplier"] = relationship("Supplier", lazy="joined")
    _service_type: Mapped["ServiceType"] = relationship("ServiceType", lazy="joined")
    file_attachments: Mapped[list["FileAttachment"]] = relationship(
        "FileAttachment", secondary="purpose_file_attachment", back_populates="purposes"
    )
    contents: Mapped[list["PurposeContent"]] = relationship(
        "PurposeContent", back_populates="purpose", cascade="all, delete-orphan"
    )
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase", back_populates="purpose", cascade="all, delete-orphan"
    )

    @property
    def supplier(self) -> str | None:
        """Return the supplier name if available."""
        return self._supplier.name if self._supplier else None

    @property
    def service_type(self) -> str | None:
        """Return the service_type name if available."""
        return self._service_type.name if self._service_type else None


class PurposeContent(Base):
    __tablename__ = "purpose_content"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    purpose_id: Mapped[int] = mapped_column(
        ForeignKey("purpose.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    purpose: Mapped["Purpose"] = relationship(back_populates="contents")
    service: Mapped["Service"] = relationship(lazy="joined")

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return self.service.name if self.service else ""

    @property
    def service_type(self) -> str:
        """Return the service type name."""
        return (
            self.service.service_type.name
            if self.service and self.service.service_type
            else ""
        )

    # Constraints
    __table_args__ = (
        UniqueConstraint("purpose_id", "service_id", name="uq_purpose_service"),
    )
