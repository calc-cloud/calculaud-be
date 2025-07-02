from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper


class TestStageTypesAPI(BaseAPITestClass):
    """Test Stage Type API endpoints using base test mixins."""

    # Configuration for base test mixins
    resource_name = "stage-types"
    resource_endpoint = f"{settings.api_v1_prefix}/stage-types"
    create_data_fixture = "sample_stage_type_data"
    instance_fixture = "sample_stage_type"
    multiple_instances_fixture = "multiple_stage_types"
    search_instances_fixture = "search_stage_types"
    search_field = "name"
    required_fields = ["name", "display_name"]

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {
            "name": "updated_stage",
            "display_name": "Updated Stage Type Name",
            "description": "Updated description",
            "value_required": True
        }

    # All basic CRUD tests are inherited from BaseAPITestClass
    # No need to rewrite test_get_empty_list, test_create_resource, etc.

    def test_create_duplicate_stage_type(
        self, test_client: TestClient, sample_stage_type
    ):
        """Test creating a stage type with duplicate name returns error."""
        duplicate_data = {
            "name": sample_stage_type.name,
            "display_name": "Different Display Name",
            "description": "Different description",
            "value_required": False
        }
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_stage_types_sorted_by_name(
        self, test_client: TestClient, multiple_stage_types
    ):
        """Test that stage types are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["name"] for item in response_data["items"]]
        expected_names = sorted([st["name"] for st in multiple_stage_types])
        assert names == expected_names

    def test_stage_type_value_required_field(
        self, test_client: TestClient, sample_stage_type_data
    ):
        """Test that value_required field works correctly."""
        # Test with value_required=True
        data_required = sample_stage_type_data.copy()
        data_required["value_required"] = True
        response = test_client.post(self.resource_endpoint, json=data_required)
        assert response.status_code == 201
        assert response.json()["value_required"] is True

        # Test with value_required=False
        data_not_required = sample_stage_type_data.copy()
        data_not_required["name"] = "different_name"
        data_not_required["value_required"] = False
        response = test_client.post(self.resource_endpoint, json=data_not_required)
        assert response.status_code == 201
        assert response.json()["value_required"] is False