import io
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.schemas import FileDownloadResponse


class TestFileUpload:
    @patch("app.files.service.s3_service.upload_file")
    def test_upload_file_success(self, mock_s3_upload, test_client: TestClient):
        """Test successful file upload."""

        mock_s3_upload.return_value = f"files/router-upload-{uuid.uuid4()}.pdf"

        response = test_client.post(
            "/api/v1/files/upload",
            files={
                "file": ("test.pdf", io.BytesIO(b"test content"), "application/pdf")
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["file_size"] == 12  # len(b"test content")
        assert "file_id" in data

    def test_upload_file_no_file(self, test_client: TestClient):
        """Test file upload without providing a file."""
        response = test_client.post("/api/v1/files/upload")

        assert response.status_code == 422  # Unprocessable Entity

    @patch("app.files.service.s3_service.upload_file")
    def test_upload_file_upload_error(self, mock_s3_upload, test_client: TestClient):
        """Test file upload with upload error."""
        from botocore.exceptions import ClientError

        mock_s3_upload.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket"}}, "upload_file"
        )

        response = test_client.post(
            "/api/v1/files/upload",
            files={
                "file": ("test.pdf", io.BytesIO(b"test content"), "application/pdf")
            },
        )

        assert response.status_code == 500
        assert "Failed to upload file" in response.json()["detail"]

    @patch("app.config.settings.max_file_size_mb", 1)  # 1MB limit
    def test_upload_file_size_exceeds_limit(self, test_client: TestClient):
        """Test file upload that exceeds size limit."""
        # Create a file larger than 1MB
        large_content = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte

        response = test_client.post(
            "/api/v1/files/upload",
            files={
                "file": ("large_file.pdf", io.BytesIO(large_content), "application/pdf")
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "File size" in data["detail"]
        assert "exceeds maximum allowed size" in data["detail"]
        assert "1 MB" in data["detail"]

    @patch("app.config.settings.max_file_size_mb", 2)  # 2MB limit
    @patch("app.files.service.s3_service.upload_file")
    def test_upload_file_size_within_limit(
        self, mock_s3_upload, test_client: TestClient
    ):
        """Test file upload within size limit."""
        mock_s3_upload.return_value = f"files/router-upload-{uuid.uuid4()}.pdf"

        # Create a file smaller than 2MB
        content = b"x" * (1024 * 1024)  # Exactly 1MB

        response = test_client.post(
            "/api/v1/files/upload",
            files={"file": ("medium_file.pdf", io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "medium_file.pdf"
        assert data["file_size"] == len(content)


class TestFileDownload:
    @patch("app.files.router.service.get_file_download_url")
    def test_get_file_download_url_success(self, mock_get_url, test_client: TestClient):
        """Test successful download URL retrieval."""
        mock_get_url.return_value = FileDownloadResponse(
            file_id=1,
            original_filename="test.pdf",
            download_url="https://s3.amazonaws.com/presigned-url",
            expires_in=3600,
        )

        response = test_client.get("/api/v1/files/1")

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == 1
        assert data["original_filename"] == "test.pdf"
        assert "presigned-url" in data["download_url"]
        assert data["expires_in"] == 3600

    @patch("app.files.router.service.get_file_download_url")
    def test_get_file_download_url_not_found(
        self, mock_get_url, test_client: TestClient
    ):
        """Test download URL retrieval for non-existent file."""
        mock_get_url.side_effect = FileNotFoundError("File with ID 999 not found")

        response = test_client.get("/api/v1/files/999")

        assert response.status_code == 404
        assert "File with ID 999 not found" in response.json()["detail"]

    @patch("app.files.router.service.get_file_download_url")
    def test_get_file_download_url_error(self, mock_get_url, test_client: TestClient):
        """Test download URL retrieval with error."""
        mock_get_url.side_effect = FileUploadError("Failed to generate download URL")

        response = test_client.get("/api/v1/files/1")

        assert response.status_code == 500
        assert "Failed to generate download URL" in response.json()["detail"]


class TestFileDelete:
    @patch("app.files.router.service.delete_file")
    def test_delete_file_success(self, mock_delete, test_client: TestClient):
        """Test successful file deletion."""
        mock_delete.return_value = True

        response = test_client.delete("/api/v1/files/1")

        assert response.status_code == 204

    @patch("app.files.router.service.delete_file")
    def test_delete_file_not_found(self, mock_delete, test_client: TestClient):
        """Test file deletion for non-existent file."""
        mock_delete.side_effect = FileNotFoundError("File with ID 999 not found")

        response = test_client.delete("/api/v1/files/999")

        assert response.status_code == 404
        assert "File with ID 999 not found" in response.json()["detail"]

    @patch("app.files.router.service.delete_file")
    def test_delete_file_error(self, mock_delete, test_client: TestClient):
        """Test file deletion with error."""
        mock_delete.side_effect = Exception("S3 deletion failed")

        response = test_client.delete("/api/v1/files/1")

        assert response.status_code == 500
        assert "S3 deletion failed" in response.json()["detail"]
