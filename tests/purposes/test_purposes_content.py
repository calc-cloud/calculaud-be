"""Test Purpose content management functionality."""

from fastapi.testclient import TestClient

from app.config import settings
from tests.utils import APITestHelper, assert_validation_error


class TestPurposeContent:
    """Test Purpose content management functionality."""

    def test_create_purpose_with_contents(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test creating a purpose with contents."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["contents"]) == 1
        assert (
            data["contents"][0]["service_id"]
            == sample_purpose_data_with_contents["contents"][0]["service_id"]
        )
        assert (
            data["contents"][0]["quantity"]
            == sample_purpose_data_with_contents["contents"][0]["quantity"]
        )

    def test_create_purpose_with_invalid_service_id(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating a purpose with invalid service_id returns 400."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [{"service_id": 999, "quantity": 2}]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 400
        assert "Service with ID 999 does not exist" in response.json()["detail"]

    def test_create_purpose_with_zero_quantity(
        self, test_client: TestClient, sample_purpose_data: dict, sample_service
    ):
        """Test creating a purpose with zero quantity returns 422."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [{"service_id": sample_service.id, "quantity": 0}]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert_validation_error(response, "quantity")

    def test_create_purpose_with_duplicate_service(
        self, test_client: TestClient, sample_purpose_data: dict, sample_service
    ):
        """Test creating a purpose with duplicate service in contents fails."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [
            {"service_id": sample_service.id, "quantity": 2},
            {"service_id": sample_service.id, "quantity": 3},
        ]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 400
        assert "already included in this purpose" in response.json()["detail"]

    def test_update_purpose_contents(
        self,
        test_client: TestClient,
        sample_purpose_data_with_contents: dict,
        sample_service,
    ):
        """Test updating purpose contents."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with contents
        purpose = helper.create_resource(sample_purpose_data_with_contents)

        # Update with new contents
        update_data = {"contents": [{"service_id": sample_service.id, "quantity": 5}]}
        updated_purpose = helper.update_resource(purpose["id"], update_data)

        assert len(updated_purpose["contents"]) == 1
        assert updated_purpose["contents"][0]["quantity"] == 5

    def test_update_purpose_contents_empty(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test updating purpose with empty contents."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with contents
        purpose = helper.create_resource(sample_purpose_data_with_contents)

        # Update with empty contents
        update_data = {"contents": []}
        updated_purpose = helper.update_resource(purpose["id"], update_data)

        assert len(updated_purpose["contents"]) == 0

    def test_update_purpose_contents_invalid_service_id(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test updating purpose with invalid service_id returns 400."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with contents
        purpose = helper.create_resource(sample_purpose_data_with_contents)

        # Update with invalid service_id
        update_data = {"contents": [{"service_id": 999, "quantity": 2}]}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose['id']}", json=update_data
        )
        assert response.status_code == 400
        assert "Service with ID 999 does not exist" in response.json()["detail"]

    def test_cascade_delete_purpose_contents(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test that purpose contents are deleted when purpose is deleted."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with contents
        purpose = helper.create_resource(sample_purpose_data_with_contents)

        # Verify purpose exists with contents
        retrieved_purpose = helper.get_resource(purpose["id"])
        assert len(retrieved_purpose["contents"]) == 1

        # Delete purpose
        helper.delete_resource(purpose["id"])

        # Verify purpose is deleted
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose['id']}")
        assert response.status_code == 404

    def test_multiple_services_in_purpose_contents(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        service_type_and_service,
    ):
        """Test creating purpose with multiple different services."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        service1_id = service_type_and_service["service"]["id"]

        # Create additional service
        service2_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={
                "name": "Service 2",
                "service_type_id": service_type_and_service["service_type"]["id"],
            },
        )
        assert service2_response.status_code == 201
        service2_id = service2_response.json()["id"]

        # Create purpose with multiple services
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [
            {"service_id": service1_id, "quantity": 2},
            {"service_id": service2_id, "quantity": 3},
        ]

        purpose = helper.create_resource(purpose_data)
        assert len(purpose["contents"]) == 2

        # Verify both services are included
        service_ids = [content["service_id"] for content in purpose["contents"]]
        assert service1_id in service_ids
        assert service2_id in service_ids

    def test_get_purpose_with_contents_includes_service_info(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test that retrieved purpose includes service information in contents."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/purposes")

        # Create purpose with contents
        purpose = helper.create_resource(sample_purpose_data_with_contents)

        # Retrieve purpose and verify service info is included
        retrieved_purpose = helper.get_resource(purpose["id"])

        assert len(retrieved_purpose["contents"]) == 1
        content = retrieved_purpose["contents"][0]

        # Verify service information is included
        assert "service_id" in content
        assert "service_name" in content
        assert content["service_name"] == "Test Service"

        # Verify quantity is preserved
        assert (
            content["quantity"]
            == sample_purpose_data_with_contents["contents"][0]["quantity"]
        )
