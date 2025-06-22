from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.purposes.models import Purpose


class FileAttachment(Base):
    __tablename__ = "file_attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    purpose_id: Mapped[int | None] = mapped_column(
        ForeignKey("purpose.id"), nullable=True, index=True
    )

    # Relationship
    purpose: Mapped["Purpose"] = relationship(
        "Purpose", back_populates="file_attachments"
    )
