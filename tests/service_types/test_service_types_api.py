from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper


class TestServiceTypesAPI(BaseAPITestClass):
    """Test Service Type API endpoints using base test mixins."""

    # Configuration for base test mixins
    resource_name = "service-types"
    resource_endpoint = f"{settings.api_v1_prefix}/service-types"
    create_data_fixture = "sample_service_type_data"
    instance_fixture = "sample_service_type"
    multiple_instances_fixture = "multiple_service_types"
    search_instances_fixture = "search_service_types"
    search_field = "name"
    required_fields = ["name"]

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {"name": "Updated Service Type Name"}

    # All basic CRUD tests are inherited from BaseAPITestClass
    # No need to rewrite test_get_empty_list, test_create_resource, etc.

    def test_create_duplicate_service_type(
        self, test_client: TestClient, sample_service_type
    ):
        """Test creating a service type with duplicate name returns error."""
        duplicate_data = {"name": sample_service_type.name}
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_service_types_sorted_by_name(
        self, test_client: TestClient, multiple_service_types
    ):
        """Test that service types are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["name"] for item in response_data["items"]]
        expected_names = sorted([st["name"] for st in multiple_service_types])
        assert names == expected_names
