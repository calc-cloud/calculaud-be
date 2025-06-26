from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app import FileAttachment


class Supplier(Base):
    __tablename__ = "supplier"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    file_icon_id: Mapped[int | None] = mapped_column(
        ForeignKey("file_attachment.id", use_alter=True), nullable=True
    )

    # Relationship to file attachment for icon
    file_icon: Mapped["FileAttachment"] = relationship(
        "FileAttachment", foreign_keys=[file_icon_id]
    )
