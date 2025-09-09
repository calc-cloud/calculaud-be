"""Budget sources API tests using BaseAPITestClass."""

from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper


class TestBudgetSourcesAPI(BaseAPITestClass):
    # Configuration for base test mixins
    resource_name = "budget_sources"
    resource_endpoint = f"{settings.api_v1_prefix}/budget-sources"
    create_data_fixture = "sample_budget_source_data"
    instance_fixture = "sample_budget_source"
    multiple_instances_fixture = "multiple_budget_sources"
    search_instances_fixture = "search_budget_sources"
    search_field = "name"

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {"name": "Updated Budget Source Name"}

    # All basic CRUD tests are inherited from BaseAPITestClass
    # No need to rewrite test_get_empty_list, test_create_resource, etc.

    def test_create_duplicate_budget_source(
        self, test_client: TestClient, sample_budget_source
    ):
        """Test creating a budget source with duplicate name returns error."""
        duplicate_data = {"name": sample_budget_source.name}
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_budget_sources_sorted_by_name(
        self, test_client: TestClient, multiple_budget_sources
    ):
        """Test that budget sources are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["name"] for item in response_data["items"]]
        expected_names = sorted(
            [budget_source.name for budget_source in multiple_budget_sources]
        )
        assert names == expected_names

    def test_budget_source_name_validation(self, test_client: TestClient):
        """Test budget source name validation."""
        # Test empty name
        response = test_client.post(self.resource_endpoint, json={"name": ""})
        assert response.status_code == 422

        # Test name too long
        long_name = "x" * 256  # Exceeds 255 character limit
        response = test_client.post(self.resource_endpoint, json={"name": long_name})
        assert response.status_code == 422

    def test_update_budget_source_with_existing_name(
        self, test_client: TestClient, multiple_budget_sources
    ):
        """Test updating budget source with existing name returns conflict."""
        # Try to update first budget source with second's name
        existing_name = multiple_budget_sources[1].name
        response = test_client.patch(
            f"{self.resource_endpoint}/{multiple_budget_sources[0].id}",
            json={"name": existing_name},
        )
        assert response.status_code == 409
