import io
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.models import FileAttachment
from app.files.service import (
    delete_file,
    get_file_download_url,
    link_files_to_purpose,
    upload_file,
)


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
        file_record = (
            db_session.query(FileAttachment).filter_by(id=result.file_id).first()
        )
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
        file_record = db_session.query(FileAttachment).first()
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
        file_record = db_session.query(FileAttachment).filter_by(id=file_id).first()
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


class TestLinkFilesToPurpose:
    def test_link_files_to_purpose_success(self, db_session):
        """Test successful file linking to purpose."""
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

        purpose_id = 123
        file_ids = [file1.id, file2.id]

        result = link_files_to_purpose(db_session, file_ids, purpose_id)

        assert result is True

        # Check files are linked to purpose
        updated_file1 = db_session.query(FileAttachment).filter_by(id=file1.id).first()
        updated_file2 = db_session.query(FileAttachment).filter_by(id=file2.id).first()

        assert updated_file1.purpose_id == purpose_id
        assert updated_file2.purpose_id == purpose_id
