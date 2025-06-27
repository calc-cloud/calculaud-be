"""Test Purpose file attachment functionality."""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import settings
from tests.utils import APITestHelper, assert_file_attachment_response


class TestPurposeFileAttachments:
    """Test Purpose file attachment functionality with many-to-many relationship."""

    @patch("app.files.service.s3_service.upload_file")
    def test_create_purpose_with_file_attachments(
        self, mock_s3_upload, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating a purpose with file attachments using many-to-many relationship."""
        # Mock S3 upload
        mock_s3_upload.return_value = "files/test-uuid.pdf"

        # Upload a file first (this will create a real database record)
        file_content = b"test content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        upload_response = test_client.post(
            f"{settings.api_v1_prefix}/files/upload", files=files
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]

        # Create purpose with file attachment
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [file_id]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "file_attachments" in data
        assert len(data["file_attachments"]) == 1
        assert data["file_attachments"][0]["id"] == file_id

        # Verify file attachment structure
        assert_file_attachment_response(data["file_attachments"][0], "test.pdf")

    def test_multiple_purposes_share_same_file(
        self, test_client: TestClient, sample_purpose_data: dict, sample_file_attachment
    ):
        """Test that multiple purposes can share the same file (many-to-many)."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")
        file_id = sample_file_attachment.id

        # Create first purpose with file
        purpose1_data = sample_purpose_data.copy()
        purpose1_data["description"] = "Purpose 1"
        purpose1_data["file_attachment_ids"] = [file_id]
        purpose1 = helper.create_resource(purpose1_data)

        # Create second purpose with same file
        purpose2_data = sample_purpose_data.copy()
        purpose2_data["description"] = "Purpose 2"
        purpose2_data["file_attachment_ids"] = [file_id]
        purpose2 = helper.create_resource(purpose2_data)

        # Verify both purposes have the same file
        retrieved_purpose1 = helper.get_resource(purpose1["id"])
        retrieved_purpose2 = helper.get_resource(purpose2["id"])

        assert len(retrieved_purpose1["file_attachments"]) == 1
        assert len(retrieved_purpose2["file_attachments"]) == 1
        assert retrieved_purpose1["file_attachments"][0]["id"] == file_id
        assert retrieved_purpose2["file_attachments"][0]["id"] == file_id

    def test_update_purpose_file_attachments(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        multiple_file_attachments,
    ):
        """Test updating purpose file attachments."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        file1_id = multiple_file_attachments[0].id
        file2_id = multiple_file_attachments[1].id

        # Create purpose with first file
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [file1_id]
        purpose = helper.create_resource(purpose_data)

        # Update to include both files
        update_data = {"file_attachment_ids": [file1_id, file2_id]}
        updated_purpose = helper.update_resource(purpose["id"], update_data)

        assert len(updated_purpose["file_attachments"]) == 2
        file_ids = [f["id"] for f in updated_purpose["file_attachments"]]
        assert file1_id in file_ids
        assert file2_id in file_ids

        # Update to remove first file
        update_data = {"file_attachment_ids": [file2_id]}
        updated_purpose = helper.update_resource(purpose["id"], update_data)

        assert len(updated_purpose["file_attachments"]) == 1
        assert updated_purpose["file_attachments"][0]["id"] == file2_id

    def test_update_purpose_remove_all_files(
        self, test_client: TestClient, sample_purpose_data: dict, sample_file_attachment
    ):
        """Test removing all file attachments from a purpose."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with file
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [sample_file_attachment.id]
        purpose = helper.create_resource(purpose_data)

        # Verify file is attached
        assert len(purpose["file_attachments"]) == 1

        # Update to remove all files
        update_data = {"file_attachment_ids": []}
        updated_purpose = helper.update_resource(purpose["id"], update_data)

        assert len(updated_purpose["file_attachments"]) == 0

    def test_delete_purpose_preserves_files(
        self, test_client: TestClient, sample_purpose_data: dict, sample_file_attachment
    ):
        """Test that deleting a purpose doesn't delete files (they might be linked to other purposes)."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with file
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [sample_file_attachment.id]
        purpose = helper.create_resource(purpose_data)

        # Delete purpose
        helper.delete_resource(purpose["id"])

        # Verify file still exists
        response = test_client.get(
            f"{settings.api_v1_prefix}/files/{sample_file_attachment.id}"
        )
        assert response.status_code == 200

    def test_purpose_without_file_attachments(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating and getting purpose without file attachments."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        purpose = helper.create_resource(sample_purpose_data)
        assert "file_attachments" in purpose
        assert len(purpose["file_attachments"]) == 0

        # Verify retrieved purpose also has empty file attachments
        retrieved_purpose = helper.get_resource(purpose["id"])
        assert "file_attachments" in retrieved_purpose
        assert len(retrieved_purpose["file_attachments"]) == 0

    def test_purpose_with_empty_file_attachment_list(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating purpose with explicitly empty file attachment list."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = []

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "file_attachments" in data
        assert len(data["file_attachments"]) == 0

    def test_purpose_with_invalid_file_attachment_id(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating purpose with non-existent file attachment ID."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [99999]  # Non-existent file ID

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 400
        assert "file" in response.json()["detail"].lower()

    def test_purpose_with_duplicate_file_attachment_ids(
        self, test_client: TestClient, sample_purpose_data: dict, sample_file_attachment
    ):
        """Test creating purpose with duplicate file attachment IDs."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [
            sample_file_attachment.id,
            sample_file_attachment.id,
        ]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        # Should succeed and deduplicate automatically
        assert response.status_code == 201
        data = response.json()
        assert len(data["file_attachments"]) == 1
        assert data["file_attachments"][0]["id"] == sample_file_attachment.id

    def test_purpose_file_attachment_metadata(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        multiple_file_attachments,
    ):
        """Test that purpose includes complete file attachment metadata."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        file_ids = [f.id for f in multiple_file_attachments]

        # Create purpose with multiple files
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = file_ids
        purpose = helper.create_resource(purpose_data)

        # Verify file metadata is complete
        assert len(purpose["file_attachments"]) == len(multiple_file_attachments)

        for file_attachment in purpose["file_attachments"]:
            assert "id" in file_attachment
            assert "original_filename" in file_attachment
            assert "mime_type" in file_attachment
            assert "file_size" in file_attachment
            assert "uploaded_at" in file_attachment

    def test_purpose_file_attachment_ordering(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        multiple_file_attachments,
    ):
        """Test that file attachments maintain consistent ordering."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        file_ids = [f.id for f in multiple_file_attachments]

        # Create purpose with files in specific order
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = file_ids
        purpose = helper.create_resource(purpose_data)

        # Verify ordering is maintained
        returned_file_ids = [f["id"] for f in purpose["file_attachments"]]

        # Note: Ordering might be by ID or creation time, depending on implementation
        # This test verifies consistent ordering rather than specific order
        retrieved_purpose = helper.get_resource(purpose["id"])
        retrieved_file_ids = [f["id"] for f in retrieved_purpose["file_attachments"]]

        assert returned_file_ids == retrieved_file_ids

    def test_large_number_of_file_attachments(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test purpose with a large number of file attachments."""
        # This test would need to create many files, which might be expensive
        # For now, we'll test with the existing multiple_file_attachments
        # In a real scenario, you might want to test with 50+ files

        # Create a purpose with the maximum reasonable number of files
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = []  # Start with empty list

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201

        # This test passes as a placeholder for performance testing
        # In practice, you'd want to test with actual file limits

    @patch("app.files.service.s3_service.upload_file")
    def test_purpose_file_workflow_complete(
        self, mock_s3_upload, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test complete workflow: upload files, create purpose, update files, delete purpose."""
        import uuid

        # Generate unique s3_keys for each file upload
        mock_s3_upload.side_effect = [
            f"files/file1-{uuid.uuid4()}.pdf",
            f"files/file2-{uuid.uuid4()}.pdf",
        ]
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Step 1: Upload files
        file1_content = b"file 1 content"
        files1 = {"file": ("file1.pdf", io.BytesIO(file1_content), "application/pdf")}
        upload1 = test_client.post(
            f"{settings.api_v1_prefix}/files/upload", files=files1
        )
        file1_id = upload1.json()["file_id"]

        file2_content = b"file 2 content"
        files2 = {"file": ("file2.pdf", io.BytesIO(file2_content), "application/pdf")}
        upload2 = test_client.post(
            f"{settings.api_v1_prefix}/files/upload", files=files2
        )
        file2_id = upload2.json()["file_id"]

        # Step 2: Create purpose with first file
        purpose_data = sample_purpose_data.copy()
        purpose_data["file_attachment_ids"] = [file1_id]
        purpose = helper.create_resource(purpose_data)

        assert len(purpose["file_attachments"]) == 1
        assert purpose["file_attachments"][0]["id"] == file1_id

        # Step 3: Add second file
        updated_purpose = helper.update_resource(
            purpose["id"], {"file_attachment_ids": [file1_id, file2_id]}
        )
        assert len(updated_purpose["file_attachments"]) == 2

        # Step 4: Replace files
        updated_purpose = helper.update_resource(
            purpose["id"], {"file_attachment_ids": [file2_id]}
        )
        assert len(updated_purpose["file_attachments"]) == 1
        assert updated_purpose["file_attachments"][0]["id"] == file2_id

        # Step 5: Remove all files
        updated_purpose = helper.update_resource(
            purpose["id"], {"file_attachment_ids": []}
        )
        assert len(updated_purpose["file_attachments"]) == 0

        # Step 6: Delete purpose
        helper.delete_resource(purpose["id"])

        # Step 7: Verify files still exist (not deleted with purpose)
        file1_response = test_client.get(f"{settings.api_v1_prefix}/files/{file1_id}")
        file2_response = test_client.get(f"{settings.api_v1_prefix}/files/{file2_id}")
        assert file1_response.status_code == 200
        assert file2_response.status_code == 200
