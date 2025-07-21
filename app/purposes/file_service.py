from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import FileAttachment
from app.files import service as file_service
from app.files.models import purpose_file_attachment
from app.purposes.exceptions import FileNotAttachedToPurpose, PurposeNotFound
from app.purposes.service import get_purpose


def upload_file_to_purpose(
    db: Session, purpose_id: int, file_obj: BinaryIO, filename: str, content_type: str
):
    """Upload a file and attach it to a specific purpose."""
    # Check if purpose exists
    db_purpose = get_purpose(db, purpose_id)
    if not db_purpose:
        raise PurposeNotFound(purpose_id)

    # Upload file using existing file service
    file_response = file_service.upload_file(db, file_obj, filename, content_type)

    # Get the file attachment and add it to the purpose
    stmt = select(FileAttachment).where(FileAttachment.id == file_response.file_id)
    file_attachment = db.execute(stmt).scalar_one()

    # Add file to purpose's file_attachments
    db_purpose.file_attachments.append(file_attachment)
    db.commit()

    return file_response


def delete_file_from_purpose(db: Session, purpose_id: int, file_id: int) -> None:
    """Remove a file from a purpose and delete the file entirely."""
    # Check if purpose exists
    db_purpose = get_purpose(db, purpose_id)
    if not db_purpose:
        raise PurposeNotFound(purpose_id)

    stmt = select(purpose_file_attachment.c.file_attachment_id).where(
        purpose_file_attachment.c.purpose_id == purpose_id,
        purpose_file_attachment.c.file_attachment_id == file_id,
    )
    attachment_exists = db.execute(stmt).scalar_one_or_none()

    if not attachment_exists:
        raise FileNotAttachedToPurpose(file_id, purpose_id)

    # Get the file attachment to remove it from the purpose
    stmt = select(FileAttachment).where(FileAttachment.id == file_id)
    file_attachment = db.execute(stmt).scalar_one()

    # Remove file from purpose's file_attachments
    db_purpose.file_attachments.remove(file_attachment)

    # Delete the file entirely using existing file service
    file_service.delete_file(db, file_id)

    db.commit()
