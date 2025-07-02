from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper


class TestServicesAPI(BaseAPITestClass):
    """Test Service API endpoints using base test mixins."""

    # Configuration for base test mixins
    resource_name = "services"
    resource_endpoint = f"{settings.api_v1_prefix}/services"
    create_data_fixture = "sample_service_data"
    instance_fixture = "sample_service"
    multiple_instances_fixture = "multiple_services"
    search_instances_fixture = "search_services"
    search_field = "name"
    required_fields = ["name", "service_type_id"]

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {"name": "Updated Service Name"}

    # All basic CRUD tests are inherited from BaseAPITestClass

    def test_create_service_invalid_service_type_id(self, test_client: TestClient):
        """Test POST /services with invalid service_type_id returns 400."""
        invalid_data = {"name": "Web Development", "service_type_id": 999}
        response = test_client.post(self.resource_endpoint, json=invalid_data)
        assert response.status_code == 400

    def test_create_duplicate_service_same_service_type(
        self, test_client: TestClient, sample_service
    ):
        """Test creating a service with duplicate name in same service type returns error."""
        duplicate_data = {
            "name": sample_service.name,
            "service_type_id": sample_service.service_type_id,
        }
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_services_sorted_by_name(self, test_client: TestClient, multiple_services):
        """Test that services are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["name"] for item in response_data["items"]]
        expected_names = sorted([service["name"] for service in multiple_services])
        assert names == expected_names

    def test_services_filter_by_service_type(
        self, test_client: TestClient, search_services
    ):
        """Test filtering services by service_type_id."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Get the service type ID from the first service
        service_type_id = search_services[0]["service_type_id"]

        # Filter by service type ID
        response_data = helper.list_resources(service_type_id=service_type_id)

        # All returned services should have the same service_type_id
        for item in response_data["items"]:
            assert item["service_type_id"] == service_type_id

    def test_create_duplicate_service_different_service_type(
        self, test_client: TestClient
    ):
        """Test creating a service with same name in different service type succeeds."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create two service types
        service_type1 = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
        ).json()

        service_type2 = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Design"}
        ).json()

        # Create service in first service type
        service1 = helper.create_resource(
            {
                "name": "Same Name Service",
                "service_type_id": service_type1["id"],
            }
        )

        # Create service with same name in different service type - should succeed
        service2 = helper.create_resource(
            {
                "name": "Same Name Service",
                "service_type_id": service_type2["id"],
            }
        )

        assert service1["name"] == service2["name"]
        assert service1["service_type_id"] != service2["service_type_id"]

    def test_cascade_delete_services_when_service_type_deleted(
        self, test_client: TestClient
    ):
        """Test that services are deleted when their service type is deleted."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create service type
        service_type = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "To Delete Type"}
        ).json()

        # Create services for this service type
        service1 = helper.create_resource(
            {"name": "Service 1", "service_type_id": service_type["id"]}
        )
        service2 = helper.create_resource(
            {"name": "Service 2", "service_type_id": service_type["id"]}
        )

        # Verify services exist
        assert helper.get_resource(service1["id"]) is not None
        assert helper.get_resource(service2["id"]) is not None

        # Delete service type
        delete_response = test_client.delete(
            f"{settings.api_v1_prefix}/service-types/{service_type['id']}"
        )
        assert delete_response.status_code == 204

        # Verify services are also deleted (cascade delete)
        response1 = test_client.get(f"{self.resource_endpoint}/{service1['id']}")
        response2 = test_client.get(f"{self.resource_endpoint}/{service2['id']}")
        assert response1.status_code == 404
        assert response2.status_code == 404
