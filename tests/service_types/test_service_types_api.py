import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.service_types.schemas import ServiceTypeCreate, ServiceTypeUpdate
from app.config import settings


class TestServiceTypesAPI:
    """Test Service Type API endpoints."""

    def test_get_service_types_empty_list(self, test_client: TestClient):
        """Test GET /service-types returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/service-types")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "has_next": False,
            "has_prev": False,
            "pages": 0,
        }

    def test_create_service_type(self, test_client: TestClient):
        """Test POST /service-types creates new service type."""
        service_type_data = {"name": "Software Development"}
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=service_type_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == service_type_data["name"]
        assert "id" in data

    def test_create_service_type_invalid_data(self, test_client: TestClient):
        """Test POST /service-types with invalid data returns 422."""
        invalid_data = {"name": ""}  # Empty name
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=invalid_data
        )
        assert response.status_code == 422

    def test_create_service_type_name_too_long(self, test_client: TestClient):
        """Test POST /service-types with name too long returns 422."""
        invalid_data = {"name": "a" * 101}  # Name longer than 100 characters
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=invalid_data
        )
        assert response.status_code == 422

    def test_get_service_type_by_id(self, test_client: TestClient):
        """Test GET /service-types/{id} returns service type."""
        # Create service type first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Test Service Type"}
        )
        service_type_id = create_response.json()["id"]

        # Get service type by ID
        response = test_client.get(f"{settings.api_v1_prefix}/service-types/{service_type_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_type_id
        assert data["name"] == "Test Service Type"

    def test_get_service_type_not_found(self, test_client: TestClient):
        """Test GET /service-types/{id} returns 404 for non-existent service type."""
        response = test_client.get(f"{settings.api_v1_prefix}/service-types/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Service type not found"

    def test_patch_service_type(self, test_client: TestClient):
        """Test PATCH /service-types/{id} patches service type."""
        # Create service type first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Original Name"}
        )
        service_type_id = create_response.json()["id"]

        # Patch service type
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/service-types/{service_type_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == service_type_id

    def test_patch_service_type_not_found(self, test_client: TestClient):
        """Test PATCH /service-types/{id} returns 404 for non-existent service type."""
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/service-types/999", json=patch_data
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Service type not found"

    def test_delete_service_type(self, test_client: TestClient):
        """Test DELETE /service-types/{id} deletes service type."""
        # Create service type first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "To Delete"}
        )
        service_type_id = create_response.json()["id"]

        # Delete service type
        response = test_client.delete(f"{settings.api_v1_prefix}/service-types/{service_type_id}")
        assert response.status_code == 204

        # Verify service type is deleted
        get_response = test_client.get(f"{settings.api_v1_prefix}/service-types/{service_type_id}")
        assert get_response.status_code == 404

    def test_delete_service_type_not_found(self, test_client: TestClient):
        """Test DELETE /service-types/{id} returns 404 for non-existent service type."""
        response = test_client.delete(f"{settings.api_v1_prefix}/service-types/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Service type not found"

    def test_get_service_types_with_pagination(self, test_client: TestClient):
        """Test GET /service-types with pagination parameters."""
        # Create multiple service types
        service_types = [
            "Software Development",
            "Hardware Procurement",
            "Consulting Services",
            "Training",
            "Maintenance",
        ]
        
        for name in service_types:
            test_client.post(
                f"{settings.api_v1_prefix}/service-types", json={"name": name}
            )

        # Test pagination
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False

        # Test second page
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True

        # Test third page
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?page=3&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_get_service_types_with_search(self, test_client: TestClient):
        """Test GET /service-types with search functionality."""
        # Create service types with different names
        service_types = [
            "Software Development",
            "Hardware Procurement",
            "Consulting Services",
            "Training Services",
            "Maintenance Services",
            "Web Development",
            "Mobile Development",
        ]
        
        for name in service_types:
            test_client.post(
                f"{settings.api_v1_prefix}/service-types", json={"name": name}
            )

        # Test search for "software"
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=software")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["name"].lower()

        # Test search for "services"
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=services")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        names = [item["name"].lower() for item in data["items"]]
        assert all("services" in name for name in names)

        # Test search for "development"
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=development")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        names = [item["name"].lower() for item in data["items"]]
        assert all("development" in name for name in names)

        # Test search with no results
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_get_service_types_search_case_insensitive(self, test_client: TestClient):
        """Test GET /service-types search is case-insensitive."""
        # Create service types
        service_types = [
            "Software Development",
            "HARDWARE PROCUREMENT",
            "consulting services",
            "Training Services",
        ]
        
        for name in service_types:
            test_client.post(
                f"{settings.api_v1_prefix}/service-types", json={"name": name}
            )

        # Test uppercase search
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=SOFTWARE")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["name"].lower()

        # Test lowercase search
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=hardware")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "hardware" in data["items"][0]["name"].lower()

        # Test mixed case search
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=CoNsUlTiNg")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "consulting" in data["items"][0]["name"].lower()

    def test_get_service_types_search_with_pagination(self, test_client: TestClient):
        """Test GET /service-types with search and pagination combined."""
        # Create service types
        service_types = [
            "Software Development",
            "Software Testing",
            "Software Maintenance",
            "Software Consulting",
            "Software Training",
        ]
        
        for name in service_types:
            test_client.post(
                f"{settings.api_v1_prefix}/service-types", json={"name": name}
            )

        # Test search with pagination
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=software&page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_next"] is True

        # Test second page
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=software&page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True

        # Test third page
        response = test_client.get(f"{settings.api_v1_prefix}/service-types?search=software&page=3&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_next"] is False

    def test_create_duplicate_service_type(self, test_client: TestClient):
        """Test creating a service type with duplicate name returns error."""
        service_type_data = {"name": "Duplicate Service"}
        
        # Create first service type
        response1 = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=service_type_data
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=service_type_data
        )
        assert response2.status_code == 400  # Should fail due to unique constraint

    def test_service_type_validation_empty_name(self, test_client: TestClient):
        """Test service type validation with empty name."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": ""}
        )
        assert response.status_code == 422

    def test_service_type_validation_missing_name(self, test_client: TestClient):
        """Test service type validation with missing name."""
        response = test_client.post(f"{settings.api_v1_prefix}/service-types", json={})
        assert response.status_code == 422

    def test_service_type_validation_invalid_name_type(self, test_client: TestClient):
        """Test service type validation with invalid name type."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": 123}
        )
        assert response.status_code == 422

    def test_patch_service_type_partial_update(self, test_client: TestClient):
        """Test PATCH /service-types/{id} with partial update."""
        # Create service type first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Original Name"}
        )
        service_type_id = create_response.json()["id"]

        # Patch with only name field
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/service-types/{service_type_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == service_type_id

    def test_service_types_are_sorted_by_name(self, test_client: TestClient):
        """Test that service types are returned sorted by name."""
        # Create service types in random order
        service_types = [
            "Zebra Service",
            "Alpha Service",
            "Beta Service",
        ]
        
        for name in service_types:
            test_client.post(
                f"{settings.api_v1_prefix}/service-types", json={"name": name}
            )

        # Get all service types
        response = test_client.get(f"{settings.api_v1_prefix}/service-types")
        assert response.status_code == 200
        data = response.json()
        
        # Verify they are sorted alphabetically
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha Service", "Beta Service", "Zebra Service"] 