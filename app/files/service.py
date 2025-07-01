from typing import BinaryIO

from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.aws.exceptions import S3DeleteError
from app.aws.service import s3_service
from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.models import FileAttachment
from app.files.schemas import FileDownloadResponse, FileUploadResponse


def upload_file(
    db: Session, file_obj: BinaryIO, filename: str, content_type: str
) -> FileUploadResponse:
    """
    Upload file to S3 and save metadata to database.

    Args:
        db: Database session
        file_obj: File object to upload
        filename: Original filename
        content_type: MIME type of the file

    Returns:
        FileUploadResponse with file metadata

    Raises:
        FileUploadError: If upload fails
    """

    try:
        # Get file size before uploading
        file_obj.seek(0, 2)
        file_size = file_obj.tell()
        file_obj.seek(0)
        
        # Upload to S3
        s3_key = s3_service.upload_file(file_obj, filename)

        # Save metadata to database
        file_attachment = FileAttachment(
            original_filename=filename,
            s3_key=s3_key,
            mime_type=content_type,
            file_size=file_size,
        )

        db.add(file_attachment)
        db.commit()
        db.refresh(file_attachment)

        return FileUploadResponse(
            file_id=file_attachment.id,
            original_filename=file_attachment.original_filename,
            mime_type=file_attachment.mime_type,
            file_size=file_attachment.file_size,
            uploaded_at=file_attachment.uploaded_at,
        )
    except ClientError as e:
        raise FileUploadError(f"Failed to upload file: {str(e)}")


def get_file_download_url(db: Session, file_id: int) -> FileDownloadResponse:
    """
    Get presigned download URL for file.

    Args:
        db: Database session
        file_id: ID of the file

    Returns:
        FileDownloadResponse with download URL

    Raises:
        FileNotFoundError: If file not found
    """
    stmt = select(FileAttachment).where(FileAttachment.id == file_id)
    file_attachment = db.execute(stmt).scalar_one_or_none()

    if not file_attachment:
        raise FileNotFoundError(f"File with ID {file_id} not found")

    try:
        download_url = s3_service.generate_presigned_url(file_attachment.s3_key)

        return FileDownloadResponse(
            file_id=file_attachment.id,
            original_filename=file_attachment.original_filename,
            download_url=download_url,
            expires_in=3600,  # 1 hour
        )
    except ClientError as e:
        raise FileUploadError(f"Failed to generate download URL: {str(e)}")


def delete_file(db: Session, file_id: int) -> bool:
    """
    Delete file from S3 and database.

    Args:
        db: Database session
        file_id: ID of the file to delete

    Returns:
        True if deletion successful

    Raises:
        FileNotFoundError: If file not found
    """
    stmt = select(FileAttachment).where(FileAttachment.id == file_id)
    file_attachment = db.execute(stmt).scalar_one_or_none()

    if not file_attachment:
        raise FileNotFoundError(f"File with ID {file_id} not found")

    try:
        # Delete from S3
        s3_service.delete_file(file_attachment.s3_key)

        # Delete from database
        db.delete(file_attachment)
        db.commit()

        return True
    except ClientError as e:
        raise S3DeleteError(f"Failed to delete file from S3: {str(e)}")


def delete_multiple_files(files: list[FileAttachment]) -> bool:
    """
    Delete all given files.

    Args:
        db: Database session
        files: files to delete

    """

    for file_attachment in files:
        try:
            # Delete from S3
            s3_service.delete_file(file_attachment.s3_key)
        except ClientError:
            # Continue with other files even if one fails
            pass

    # Delete all files from database (will be handled by cascade delete)
    return True
