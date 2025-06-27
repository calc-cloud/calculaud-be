"""Refactored Supplier tests using base test mixins - Example of refactoring pattern."""

from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper, assert_file_attachment_response


class TestSuppliersApi(BaseAPITestClass):
    # Configuration for base test mixins
    resource_name = "suppliers"
    resource_endpoint = f"{settings.api_v1_prefix}/suppliers"
    create_data_fixture = "sample_supplier_data"
    instance_fixture = "sample_supplier"
    multiple_instances_fixture = "multiple_suppliers"
    search_instances_fixture = "search_suppliers"
    search_field = "name"

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {"name": "Updated Supplier Name"}

    # All basic CRUD tests are inherited from BaseAPITestClass
    # No need to rewrite test_get_empty_list, test_create_resource, etc.

    def test_create_duplicate_supplier(self, test_client: TestClient, sample_supplier):
        """Test creating a supplier with duplicate name returns error."""
        duplicate_data = {"name": sample_supplier.name}
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_suppliers_sorted_by_name(
        self, test_client: TestClient, multiple_suppliers
    ):
        """Test that suppliers are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["name"] for item in response_data["items"]]
        expected_names = sorted([supplier.name for supplier in multiple_suppliers])
        assert names == expected_names

    """Test Supplier file icon functionality."""

    def test_supplier_with_file_icon(
        self, test_client: TestClient, sample_file_attachment, multiple_file_attachments
    ):
        """Test creating and updating supplier with file icon."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create supplier with file icon
        supplier_data = {
            "name": "Tech Corp with Icon",
            "file_icon_id": sample_file_attachment.id,
        }
        supplier = helper.create_resource(supplier_data)

        assert supplier["file_icon_id"] == sample_file_attachment.id
        assert supplier["file_icon"] is not None
        assert_file_attachment_response(
            supplier["file_icon"], sample_file_attachment.original_filename
        )

        # Update with different file icon
        updated_supplier = helper.update_resource(
            supplier["id"], {"file_icon_id": multiple_file_attachments[1].id}
        )
        assert updated_supplier["file_icon_id"] == multiple_file_attachments[1].id
        assert_file_attachment_response(
            updated_supplier["file_icon"],
            multiple_file_attachments[1].original_filename,
        )

        # Remove file icon
        updated_supplier = helper.update_resource(
            supplier["id"], {"file_icon_id": None}
        )
        assert updated_supplier["file_icon_id"] is None
        assert updated_supplier["file_icon"] is None

    def test_supplier_with_invalid_file_icon(
        self, test_client: TestClient, sample_file_attachment
    ):
        """Test creating supplier with non-existent file icon ID."""
        invalid_file_id = sample_file_attachment.id + 99999
        supplier_data = {"name": "Tech Corp", "file_icon_id": invalid_file_id}

        response = test_client.post(self.resource_endpoint, json=supplier_data)
        assert response.status_code == 400
        assert f"File with ID {invalid_file_id} not found" in response.json()["detail"]

    def test_supplier_with_null_file_icon(self, test_client: TestClient):
        """Test creating supplier with null file icon ID."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        supplier_data = {"name": "Tech Corp No Icon", "file_icon_id": None}
        supplier = helper.create_resource(supplier_data)

        assert supplier["file_icon_id"] is None
        assert supplier["file_icon"] is None
