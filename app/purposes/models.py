from datetime import date, datetime
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
    event,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.files.models import FileAttachment
    from app.hierarchies.models import Hierarchy
    from app.purchases.models import Purchase
    from app.responsible_authorities.models import ResponsibleAuthority
    from app.service_types.models import ServiceType
    from app.services.models import Service
    from app.suppliers.models import Supplier


class StatusEnum(PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SIGNED = "SIGNED"
    PARTIALLY_SUPPLIED = "PARTIALLY_SUPPLIED"


class Purpose(Base):
    __tablename__ = "purpose"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    description: Mapped[str | None] = mapped_column(
        String(2000), nullable=True, index=True
    )
    creation_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum), nullable=False, index=True
    )
    comments: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_modified: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
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

    @property
    def pending_authority(self) -> "ResponsibleAuthority | None":
        """
        Return the responsible authority for the highest priority incomplete stage.

        This property uses the same SQL logic as the filtering functions to ensure
        consistency. It prioritizes incomplete stages first, then sorts by priority
        ascending, with deterministic tie-breaking by stage_type.id.

        NOTE: Must use the same logic as get_pending_authority_query() in
        app.purposes.pending_authority_utils to maintain consistency.
        """
        from app.purposes.pending_authority_utils import get_pending_authority_object

        # Get the session from the object to execute the query
        session = object_session(self)
        if not session:
            return None

        return get_pending_authority_object(session, self.id)


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


def update_purpose_last_modified(connection, purpose_id: int) -> None:
    """Update the last_modified timestamp for a Purpose."""
    connection.execute(
        text("UPDATE purpose SET last_modified = :now WHERE id = :purpose_id"),
        {"now": datetime.now(), "purpose_id": purpose_id},
    )


# Event listeners for Purpose relationships
@event.listens_for(Purpose.file_attachments, "append")
@event.listens_for(Purpose.file_attachments, "remove")
@event.listens_for(Purpose.contents, "append")
@event.listens_for(Purpose.contents, "remove")
@event.listens_for(Purpose.purchases, "append")
@event.listens_for(Purpose.purchases, "remove")
def _update_purpose_on_relationship_change(target, value, initiator):
    """Update Purpose.last_modified when relationships are modified."""
    session = object_session(target)
    if session:
        connection = session.connection()
        update_purpose_last_modified(connection, target.id)


# Event listeners for PurposeContent
@event.listens_for(PurposeContent, "after_insert")
@event.listens_for(PurposeContent, "after_update")
@event.listens_for(PurposeContent, "after_delete")
def _update_purpose_on_content_change(
    _mapper, connection, target: PurposeContent
) -> None:
    """Update Purpose.last_modified when PurposeContent changes."""
    if hasattr(target, "purpose_id") and target.purpose_id:
        update_purpose_last_modified(connection, target.purpose_id)
