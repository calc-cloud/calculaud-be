from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass


class TestResponsibleAuthoritiesAPI(BaseAPITestClass):
    """Test ResponsibleAuthority API endpoints using base test mixins."""

    # Configuration for base test mixins
    resource_name = "responsible-authorities"
    resource_endpoint = f"{settings.api_v1_prefix}/responsible-authorities"
    create_data_fixture = "sample_responsible_authority_data"
    instance_fixture = "sample_responsible_authority"
    multiple_instances_fixture = "multiple_responsible_authorities"
    search_instances_fixture = "search_responsible_authorities"
    search_field = "name"
    required_fields = ["name"]

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {
            "name": "Updated Authority",
            "description": "Updated description",
        }

    # All basic CRUD tests are inherited from BaseAPITestClass

    def test_create_duplicate_responsible_authority(
        self, test_client: TestClient, sample_responsible_authority
    ):
        """Test creating a responsible authority with duplicate name returns error."""
        duplicate_data = {
            "name": sample_responsible_authority.name,
            "description": "Different description",
        }
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_responsible_authorities_sorted_by_name(
        self, test_client: TestClient, multiple_responsible_authorities
    ):
        """Test that responsible authorities are returned sorted by name."""
        response = test_client.get(self.resource_endpoint)
        assert response.status_code == 200

        data = response.json()
        names = [item["name"] for item in data["items"]]
        expected_names = sorted([ra["name"] for ra in multiple_responsible_authorities])
        assert names == expected_names
