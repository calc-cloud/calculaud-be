from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purposes.models import Purpose

# Association table for many-to-many relationship between purposes and file attachments
purpose_file_attachment = Table(
    "purpose_file_attachment",
    Base.metadata,
    Column(
        "purpose_id", ForeignKey("purpose.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "file_attachment_id",
        ForeignKey("file_attachment.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class FileAttachment(Base):
    __tablename__ = "file_attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, server_default=func.now()
    )

    # Many-to-many relationship with purposes
    purposes: Mapped[list["Purpose"]] = relationship(
        "Purpose", secondary=purpose_file_attachment, back_populates="file_attachments"
    )
