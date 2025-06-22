from fastapi.testclient import TestClient

from app.config import settings


class TestServicesAPI:
    """Test Service API endpoints."""

    def test_get_services_empty_list(self, test_client: TestClient):
        """Test GET /services returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/services")
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

    def test_create_service(self, test_client: TestClient):
        """Test POST /services creates new service."""
        # First create a service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types",
            json={"name": "Software Development"},
        )
        service_type_id = service_type_response.json()["id"]

        service_data = {"name": "Web Development", "service_type_id": service_type_id}
        response = test_client.post(
            f"{settings.api_v1_prefix}/services", json=service_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == service_data["name"]
        assert data["service_type_id"] == service_type_id
        assert "id" in data

    def test_create_service_invalid_data(self, test_client: TestClient):
        """Test POST /services with invalid data returns 422."""
        invalid_data = {"name": ""}  # Empty name
        response = test_client.post(
            f"{settings.api_v1_prefix}/services", json=invalid_data
        )
        assert response.status_code == 422

    def test_create_service_missing_service_type_id(self, test_client: TestClient):
        """Test POST /services with missing service_type_id returns 422."""
        invalid_data = {"name": "Web Development"}  # Missing service_type_id
        response = test_client.post(
            f"{settings.api_v1_prefix}/services", json=invalid_data
        )
        assert response.status_code == 422

    def test_create_service_invalid_service_type_id(self, test_client: TestClient):
        """Test POST /services with invalid service_type_id returns 400."""
        invalid_data = {
            "name": "Web Development",
            "service_type_id": 999,
        }  # Non-existent service type
        response = test_client.post(
            f"{settings.api_v1_prefix}/services", json=invalid_data
        )
        assert response.status_code == 400

    def test_get_service_by_id(self, test_client: TestClient):
        """Test GET /services/{id} returns service."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types",
            json={"name": "Test Service Type"},
        )
        service_type_id = service_type_response.json()["id"]

        # Create service
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Test Service", "service_type_id": service_type_id},
        )
        service_id = create_response.json()["id"]

        # Get service by ID
        response = test_client.get(f"{settings.api_v1_prefix}/services/{service_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_id
        assert data["name"] == "Test Service"
        assert data["service_type_id"] == service_type_id

    def test_get_service_not_found(self, test_client: TestClient):
        """Test GET /services/{id} returns 404 for non-existent service."""
        response = test_client.get(f"{settings.api_v1_prefix}/services/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Service not found"

    def test_patch_service(self, test_client: TestClient):
        """Test PATCH /services/{id} patches service."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Original Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create service
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Original Name", "service_type_id": service_type_id},
        )
        service_id = create_response.json()["id"]

        # Patch service
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/services/{service_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == service_id
        assert data["service_type_id"] == service_type_id

    def test_patch_service_not_found(self, test_client: TestClient):
        """Test PATCH /services/{id} returns 404 for non-existent service."""
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/services/999", json=patch_data
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Service not found"

    def test_delete_service(self, test_client: TestClient):
        """Test DELETE /services/{id} deletes service."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Delete Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create service
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "To Delete", "service_type_id": service_type_id},
        )
        service_id = create_response.json()["id"]

        # Delete service
        response = test_client.delete(f"{settings.api_v1_prefix}/services/{service_id}")
        assert response.status_code == 204

        # Verify service is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/services/{service_id}"
        )
        assert get_response.status_code == 404

    def test_delete_service_not_found(self, test_client: TestClient):
        """Test DELETE /services/{id} returns 404 for non-existent service."""
        response = test_client.delete(f"{settings.api_v1_prefix}/services/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Service not found"

    def test_get_services_with_pagination(self, test_client: TestClient):
        """Test GET /services with pagination parameters."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Pagination Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create multiple services
        services = [
            "Web Development",
            "Mobile Development",
            "API Development",
            "Database Design",
            "System Architecture",
        ]

        for name in services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type_id},
            )

        # Test pagination
        response = test_client.get(f"{settings.api_v1_prefix}/services?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False

        # Test second page
        response = test_client.get(f"{settings.api_v1_prefix}/services?page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True

        # Test third page
        response = test_client.get(f"{settings.api_v1_prefix}/services?page=3&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_get_services_with_search(self, test_client: TestClient):
        """Test GET /services with search functionality."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Search Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create services with different names
        services = [
            "Web Development",
            "Mobile Development",
            "API Development",
            "Database Design",
            "System Architecture",
            "Frontend Development",
            "Backend Development",
        ]

        for name in services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type_id},
            )

        # Test search for "development"
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?search=development"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        names = [item["name"].lower() for item in data["items"]]
        assert all("development" in name for name in names)

        # Test search for "design"
        response = test_client.get(f"{settings.api_v1_prefix}/services?search=design")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "design" in data["items"][0]["name"].lower()

        # Test search with no results
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?search=nonexistent"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_get_services_search_case_insensitive(self, test_client: TestClient):
        """Test GET /services search is case-insensitive."""
        # Create service type first
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Case Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create services
        services = [
            "Web Development",
            "MOBILE DEVELOPMENT",
            "api development",
            "Database Design",
        ]

        for name in services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type_id},
            )

        # Test uppercase search
        response = test_client.get(f"{settings.api_v1_prefix}/services?search=WEB")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "web" in data["items"][0]["name"].lower()

        # Test lowercase search
        response = test_client.get(f"{settings.api_v1_prefix}/services?search=mobile")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "mobile" in data["items"][0]["name"].lower()

        # Test mixed case search
        response = test_client.get(f"{settings.api_v1_prefix}/services?search=DaTaBaSe")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "database" in data["items"][0]["name"].lower()

    def test_get_services_filter_by_service_type_id(self, test_client: TestClient):
        """Test GET /services with service_type_id filter."""
        # Create two service types
        service_type1_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
        )
        service_type1_id = service_type1_response.json()["id"]

        service_type2_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Design"}
        )
        service_type2_id = service_type2_response.json()["id"]

        # Create services for both types
        dev_services = ["Web Development", "Mobile Development", "API Development"]
        design_services = ["UI Design", "UX Design"]

        for name in dev_services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type1_id},
            )

        for name in design_services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type2_id},
            )

        # Test filter by first service type
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?service_type_id={service_type1_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert all(
            item["service_type_id"] == service_type1_id for item in data["items"]
        )

        # Test filter by second service type
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?service_type_id={service_type2_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert all(
            item["service_type_id"] == service_type2_id for item in data["items"]
        )

        # Test filter by non-existent service type
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?service_type_id=999"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_get_services_combined_filters(self, test_client: TestClient):
        """Test GET /services with combined search and service_type_id filter."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create services
        services = [
            "Web Development",
            "Mobile Development",
            "Web Design",
            "Mobile Testing",
        ]

        for name in services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type_id},
            )

        # Test combined search and service_type_id filter
        response = test_client.get(
            f"{settings.api_v1_prefix}/services?search=development&service_type_id={service_type_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all("development" in item["name"].lower() for item in data["items"])
        assert all(item["service_type_id"] == service_type_id for item in data["items"])

    def test_create_duplicate_service_same_service_type(self, test_client: TestClient):
        """Test creating a service with duplicate name in same service type returns error."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
        )
        service_type_id = service_type_response.json()["id"]

        service_data = {"name": "Duplicate Service", "service_type_id": service_type_id}

        # Create first service
        response1 = test_client.post(
            f"{settings.api_v1_prefix}/services", json=service_data
        )
        assert response1.status_code == 201

        # Try to create duplicate in same service type
        response2 = test_client.post(
            f"{settings.api_v1_prefix}/services", json=service_data
        )
        assert response2.status_code == 409  # Should fail due to unique constraint

    def test_create_duplicate_service_different_service_type(
        self, test_client: TestClient
    ):
        """Test creating a service with same name in different service type succeeds."""
        # Create two service types
        service_type1_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
        )
        service_type1_id = service_type1_response.json()["id"]

        service_type2_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Design"}
        )
        service_type2_id = service_type2_response.json()["id"]

        # Create service in first service type
        service_data1 = {
            "name": "Same Name Service",
            "service_type_id": service_type1_id,
        }
        response1 = test_client.post(
            f"{settings.api_v1_prefix}/services", json=service_data1
        )
        assert response1.status_code == 201

        # Create service with same name in different service type - should succeed
        service_data2 = {
            "name": "Same Name Service",
            "service_type_id": service_type2_id,
        }
        response2 = test_client.post(
            f"{settings.api_v1_prefix}/services", json=service_data2
        )
        assert response2.status_code == 201

    def test_cascade_delete_services_when_service_type_deleted(
        self, test_client: TestClient
    ):
        """Test that services are deleted when their service type is deleted."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "To Delete Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create services for this service type
        service1_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Service 1", "service_type_id": service_type_id},
        )
        service1_id = service1_response.json()["id"]

        service2_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Service 2", "service_type_id": service_type_id},
        )
        service2_id = service2_response.json()["id"]

        # Verify services exist
        assert (
            test_client.get(
                f"{settings.api_v1_prefix}/services/{service1_id}"
            ).status_code
            == 200
        )
        assert (
            test_client.get(
                f"{settings.api_v1_prefix}/services/{service2_id}"
            ).status_code
            == 200
        )

        # Delete service type
        delete_response = test_client.delete(
            f"{settings.api_v1_prefix}/service-types/{service_type_id}"
        )
        assert delete_response.status_code == 204

        # Verify services are also deleted (cascade delete)
        assert (
            test_client.get(
                f"{settings.api_v1_prefix}/services/{service1_id}"
            ).status_code
            == 404
        )
        assert (
            test_client.get(
                f"{settings.api_v1_prefix}/services/{service2_id}"
            ).status_code
            == 404
        )

    def test_services_are_sorted_by_name(self, test_client: TestClient):
        """Test that services are returned sorted by name."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Sort Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create services in random order
        services = [
            "Zebra Service",
            "Alpha Service",
            "Beta Service",
        ]

        for name in services:
            test_client.post(
                f"{settings.api_v1_prefix}/services",
                json={"name": name, "service_type_id": service_type_id},
            )

        # Get all services
        response = test_client.get(f"{settings.api_v1_prefix}/services")
        assert response.status_code == 200
        data = response.json()

        # Verify they are sorted alphabetically
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha Service", "Beta Service", "Zebra Service"]

    def test_service_validation_empty_name(self, test_client: TestClient):
        """Test service validation with empty name."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Validation Type"}
        )
        service_type_id = service_type_response.json()["id"]

        response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "", "service_type_id": service_type_id},
        )
        assert response.status_code == 422

    def test_service_validation_missing_name(self, test_client: TestClient):
        """Test service validation with missing name."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Validation Type"}
        )
        service_type_id = service_type_response.json()["id"]

        response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"service_type_id": service_type_id},
        )
        assert response.status_code == 422

    def test_service_validation_invalid_name_type(self, test_client: TestClient):
        """Test service validation with invalid name type."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Validation Type"}
        )
        service_type_id = service_type_response.json()["id"]

        response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": 123, "service_type_id": service_type_id},
        )
        assert response.status_code == 422

    def test_patch_service_partial_update(self, test_client: TestClient):
        """Test PATCH /services/{id} with partial update."""
        # Create service type
        service_type_response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json={"name": "Patch Type"}
        )
        service_type_id = service_type_response.json()["id"]

        # Create service
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Original Name", "service_type_id": service_type_id},
        )
        service_id = create_response.json()["id"]

        # Patch with only name field
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/services/{service_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == service_id
        assert data["service_type_id"] == service_type_id
