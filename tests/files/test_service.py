import io
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from sqlalchemy import select

from app import Purpose, StatusEnum
from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.models import FileAttachment
from app.files.service import delete_file, get_file_download_url, upload_file


class TestUploadFile:
    @patch("app.files.service.s3_service.upload_file")
    def test_upload_file_success(self, mock_s3_upload, db_session):
        """Test successful file upload."""
        mock_s3_upload.return_value = "files/test-uuid.pdf"

        file_obj = io.BytesIO(b"test content")
        result = upload_file(db_session, file_obj, "test.pdf", "application/pdf")

        assert result.original_filename == "test.pdf"
        assert result.mime_type == "application/pdf"
        assert result.file_size == len(b"test content")
        assert result.message == "File uploaded successfully"

        # Check database record was created
        stmt = select(FileAttachment).where(FileAttachment.id == result.file_id)
        file_record = db_session.execute(stmt).scalar_one_or_none()
        assert file_record is not None
        assert file_record.original_filename == "test.pdf"

    @patch("app.files.service.s3_service.upload_file")
    def test_upload_file_s3_error(self, mock_s3_upload, db_session):
        """Test file upload with S3 error."""
        mock_s3_upload.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket"}}, "upload_file"
        )

        file_obj = io.BytesIO(b"test content")

        with pytest.raises(FileUploadError):
            upload_file(db_session, file_obj, "test.pdf", "application/pdf")

        # Check no database record was created
        stmt = select(FileAttachment)
        file_record = db_session.execute(stmt).scalar_one_or_none()
        assert file_record is None


class TestGetFileDownloadUrl:
    @patch("app.files.service.s3_service.generate_presigned_url")
    def test_get_file_download_url_success(self, mock_presigned_url, db_session):
        """Test successful download URL generation."""
        mock_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"

        # Create a file record in database
        file_attachment = FileAttachment(
            original_filename="test.pdf",
            s3_key="files/test-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        db_session.add(file_attachment)
        db_session.commit()

        result = get_file_download_url(db_session, file_attachment.id)

        assert result.file_id == file_attachment.id
        assert result.original_filename == "test.pdf"
        assert result.download_url == "https://s3.amazonaws.com/presigned-url"
        assert result.expires_in == 3600

    def test_get_file_download_url_not_found(self, db_session):
        """Test download URL generation for non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_file_download_url(db_session, 999)

    @patch("app.files.service.s3_service.generate_presigned_url")
    def test_get_file_download_url_s3_error(self, mock_presigned_url, db_session):
        """Test download URL generation with S3 error."""
        mock_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "generate_presigned_url"
        )

        # Create a file record in database
        file_attachment = FileAttachment(
            original_filename="test.pdf",
            s3_key="files/test-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        db_session.add(file_attachment)
        db_session.commit()

        with pytest.raises(FileUploadError):
            get_file_download_url(db_session, file_attachment.id)


class TestDeleteFile:
    @patch("app.files.service.s3_service.delete_file")
    def test_delete_file_success(self, mock_s3_delete, db_session):
        """Test successful file deletion."""
        mock_s3_delete.return_value = True

        # Create a file record in database
        file_attachment = FileAttachment(
            original_filename="test.pdf",
            s3_key="files/test-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        db_session.add(file_attachment)
        db_session.commit()
        file_id = file_attachment.id

        result = delete_file(db_session, file_id)

        assert result is True

        # Check file was deleted from database
        stmt = select(FileAttachment).where(FileAttachment.id == file_id)
        file_record = db_session.execute(stmt).scalar_one_or_none()
        assert file_record is None

    def test_delete_file_not_found(self, db_session):
        """Test file deletion for non-existent file."""
        with pytest.raises(FileNotFoundError):
            delete_file(db_session, 999)

    @patch("app.files.service.s3_service.delete_file")
    def test_delete_file_s3_error(self, mock_s3_delete, db_session):
        """Test file deletion with S3 error."""
        mock_s3_delete.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "delete_object"
        )

        # Create a file record in database
        file_attachment = FileAttachment(
            original_filename="test.pdf",
            s3_key="files/test-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        db_session.add(file_attachment)
        db_session.commit()

        from app.aws.exceptions import S3DeleteError

        with pytest.raises(S3DeleteError):
            delete_file(db_session, file_attachment.id)


class TestFilePurposeManyToManyRelationship:
    def test_direct_many_to_many_relationship(self, db_session, sample_purpose):
        """Test direct many-to-many relationship between files and purposes."""
        # Create file records
        file1 = FileAttachment(
            original_filename="test1.pdf",
            s3_key="files/test1-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        file2 = FileAttachment(
            original_filename="test2.pdf",
            s3_key="files/test2-uuid.pdf",
            mime_type="application/pdf",
            file_size=2048,
        )
        db_session.add_all([file1, file2])
        db_session.commit()

        # Directly link files to purpose using the many-to-many relationship
        sample_purpose.file_attachments.extend([file1, file2])
        db_session.commit()

        # Verify the relationship works both ways
        db_session.refresh(sample_purpose)
        db_session.refresh(file1)
        db_session.refresh(file2)

        # Check files are linked to purpose
        linked_file_ids = {f.id for f in sample_purpose.file_attachments}
        assert file1.id in linked_file_ids
        assert file2.id in linked_file_ids

        # Check purpose is linked to files (reverse relationship)
        assert sample_purpose in file1.purposes
        assert sample_purpose in file2.purposes

    def test_file_linked_to_multiple_purposes(
        self, db_session, sample_purpose, sample_hierarchy
    ):
        """Test that a single file can be linked to multiple purposes (many-to-many)."""

        # Create a second purpose
        purpose2 = Purpose(
            hierarchy_id=sample_hierarchy.id,
            status=StatusEnum.IN_PROGRESS,
            description="Second purpose",
        )
        db_session.add(purpose2)
        db_session.commit()

        # Create a file
        shared_file = FileAttachment(
            original_filename="shared.pdf",
            s3_key="files/shared-uuid.pdf",
            mime_type="application/pdf",
            file_size=1024,
        )
        db_session.add(shared_file)
        db_session.commit()

        # Link the same file to both purposes
        sample_purpose.file_attachments.append(shared_file)
        purpose2.file_attachments.append(shared_file)
        db_session.commit()

        # Verify the file is linked to both purposes
        db_session.refresh(sample_purpose)
        db_session.refresh(purpose2)
        db_session.refresh(shared_file)

        assert shared_file in sample_purpose.file_attachments
        assert shared_file in purpose2.file_attachments

        # Verify reverse relationships
        assert sample_purpose in shared_file.purposes
        assert purpose2 in shared_file.purposes
        assert len(shared_file.purposes) == 2
