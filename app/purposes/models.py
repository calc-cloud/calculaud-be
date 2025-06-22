from datetime import UTC, date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.emfs.models import EMF
    from app.files.models import FileAttachment
    from app.hierarchies.models import Hierarchy
    from app.service_types.models import ServiceType
    from app.suppliers.models import Supplier


class StatusEnum(PyEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Purpose(Base):
    __tablename__ = "purpose"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True, index=True)
    content: Mapped[str | None] = mapped_column(String(2000), nullable=True, index=True)
    creation_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False, index=True)
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
        "Hierarchy", back_populates="purposes"
    )
    _supplier: Mapped["Supplier"] = relationship("Supplier")
    _service_type: Mapped["ServiceType"] = relationship("ServiceType")
    emfs: Mapped[list["EMF"]] = relationship(
        "EMF", back_populates="purpose", cascade="all, delete-orphan"
    )
    file_attachments: Mapped[list["FileAttachment"]] = relationship(
        "FileAttachment", back_populates="purpose", cascade="all, delete-orphan"
    )

    @property
    def supplier(self) -> str | None:
        """Return the supplier name if available."""
        return self._supplier.name if self._supplier else None

    @property
    def service_type(self) -> str | None:
        """Return the service_type name if available."""
        return self._service_type.name if self._service_type else None
