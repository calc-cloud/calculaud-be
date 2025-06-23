from fastapi.testclient import TestClient

from app.config import settings


class TestSuppliersAPI:
    """Test Supplier API endpoints."""

    def test_get_suppliers_empty_list(self, test_client: TestClient):
        """Test GET /suppliers returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 100,
            "has_next": False,
            "has_prev": False,
            "pages": 0,
        }

    def test_create_supplier(self, test_client: TestClient):
        """Test POST /suppliers creates new supplier."""
        supplier_data = {"name": "Tech Solutions Inc"}
        response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json=supplier_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == supplier_data["name"]
        assert "id" in data

    def test_create_supplier_invalid_data(self, test_client: TestClient):
        """Test POST /suppliers with invalid data returns 422."""
        invalid_data = {"name": ""}  # Empty name
        response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json=invalid_data
        )
        assert response.status_code == 422

    def test_create_supplier_name_too_long(self, test_client: TestClient):
        """Test POST /suppliers with name too long returns 422."""
        invalid_data = {"name": "a" * 101}  # Name longer than 100 characters
        response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json=invalid_data
        )
        assert response.status_code == 422

    def test_get_supplier_by_id(self, test_client: TestClient):
        """Test GET /suppliers/{id} returns supplier."""
        # Create supplier first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Test Supplier"}
        )
        supplier_id = create_response.json()["id"]

        # Get supplier by ID
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers/{supplier_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id
        assert data["name"] == "Test Supplier"

    def test_get_supplier_not_found(self, test_client: TestClient):
        """Test GET /suppliers/{id} returns 404 for non-existent supplier."""
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Supplier not found"

    def test_patch_supplier(self, test_client: TestClient):
        """Test PATCH /suppliers/{id} patches supplier."""
        # Create supplier first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Original Name"}
        )
        supplier_id = create_response.json()["id"]

        # Patch supplier
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/suppliers/{supplier_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == supplier_id

    def test_patch_supplier_not_found(self, test_client: TestClient):
        """Test PATCH /suppliers/{id} returns 404 for non-existent supplier."""
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/suppliers/999", json=patch_data
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Supplier with ID 999 not found"

    def test_delete_supplier(self, test_client: TestClient):
        """Test DELETE /suppliers/{id} deletes supplier."""
        # Create supplier first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "To Delete"}
        )
        supplier_id = create_response.json()["id"]

        # Delete supplier
        response = test_client.delete(
            f"{settings.api_v1_prefix}/suppliers/{supplier_id}"
        )
        assert response.status_code == 204

        # Verify supplier is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers/{supplier_id}"
        )
        assert get_response.status_code == 404

    def test_delete_supplier_not_found(self, test_client: TestClient):
        """Test DELETE /suppliers/{id} returns 404 for non-existent supplier."""
        response = test_client.delete(f"{settings.api_v1_prefix}/suppliers/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Supplier with ID 999 not found"

    def test_get_suppliers_with_pagination(self, test_client: TestClient):
        """Test GET /suppliers with pagination parameters."""
        # Create multiple suppliers
        suppliers = [
            "Tech Solutions Inc",
            "Hardware Plus",
            "Software Services Ltd",
            "IT Consulting",
            "Digital Solutions",
        ]

        for name in suppliers:
            test_client.post(f"{settings.api_v1_prefix}/suppliers", json={"name": name})

        # Test pagination
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False

        # Test second page
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True

        # Test third page
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?page=3&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_get_suppliers_with_search(self, test_client: TestClient):
        """Test GET /suppliers with search functionality."""
        # Create suppliers with different names
        suppliers = [
            "Tech Solutions Inc",
            "Hardware Plus",
            "Software Services Ltd",
            "IT Consulting",
            "Digital Solutions",
            "Apple Computer",
            "Microsoft Corporation",
        ]

        for name in suppliers:
            test_client.post(f"{settings.api_v1_prefix}/suppliers", json={"name": name})

        # Test search for "tech"
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?search=tech")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "tech" in data["items"][0]["name"].lower()

        # Test search for "solutions"
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=solutions"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        names = [item["name"].lower() for item in data["items"]]
        assert all("solutions" in name for name in names)

        # Test search for "inc"
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?search=inc")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "inc" in data["items"][0]["name"].lower()

        # Test search with no results
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=nonexistent"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_get_suppliers_search_case_insensitive(self, test_client: TestClient):
        """Test GET /suppliers search is case-insensitive."""
        # Create suppliers
        suppliers = [
            "Tech Solutions Inc",
            "HARDWARE PLUS",
            "software services ltd",
            "It Consulting",
        ]

        for name in suppliers:
            test_client.post(f"{settings.api_v1_prefix}/suppliers", json={"name": name})

        # Test uppercase search
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers?search=TECH")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "tech" in data["items"][0]["name"].lower()

        # Test lowercase search
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=hardware"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "hardware" in data["items"][0]["name"].lower()

        # Test mixed case search
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=SoFtWaRe"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["name"].lower()

    def test_get_suppliers_search_with_pagination(self, test_client: TestClient):
        """Test GET /suppliers with search and pagination combined."""
        # Create suppliers
        suppliers = [
            "Tech Solutions Inc",
            "Tech Hardware Plus",
            "Software Tech Services",
            "IT Tech Consulting",
            "Digital Tech Solutions",
        ]

        for name in suppliers:
            test_client.post(f"{settings.api_v1_prefix}/suppliers", json={"name": name})

        # Test search with pagination
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=tech&page=1&limit=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_next"] is True

        # Test second page
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=tech&page=2&limit=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True

        # Test third page
        response = test_client.get(
            f"{settings.api_v1_prefix}/suppliers?search=tech&page=3&limit=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_next"] is False

    def test_create_duplicate_supplier(self, test_client: TestClient):
        """Test creating a supplier with duplicate name returns error."""
        supplier_data = {"name": "Duplicate Supplier"}

        # Create first supplier
        response1 = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json=supplier_data
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json=supplier_data
        )
        assert response2.status_code == 409  # Should fail due to unique constraint

    def test_supplier_validation_empty_name(self, test_client: TestClient):
        """Test supplier validation with empty name."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": ""}
        )
        assert response.status_code == 422

    def test_supplier_validation_missing_name(self, test_client: TestClient):
        """Test supplier validation with missing name."""
        response = test_client.post(f"{settings.api_v1_prefix}/suppliers", json={})
        assert response.status_code == 422

    def test_supplier_validation_invalid_name_type(self, test_client: TestClient):
        """Test supplier validation with invalid name type."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": 123}
        )
        assert response.status_code == 422

    def test_patch_supplier_partial_update(self, test_client: TestClient):
        """Test PATCH /suppliers/{id} with partial update."""
        # Create supplier first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Original Name"}
        )
        supplier_id = create_response.json()["id"]

        # Patch with only name field
        patch_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/suppliers/{supplier_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == supplier_id

    def test_suppliers_are_sorted_by_name(self, test_client: TestClient):
        """Test that suppliers are returned sorted by name."""
        # Create suppliers in random order
        suppliers = [
            "Zebra Corp",
            "Alpha Industries",
            "Beta Solutions",
        ]

        for name in suppliers:
            test_client.post(f"{settings.api_v1_prefix}/suppliers", json={"name": name})

        # Get all suppliers
        response = test_client.get(f"{settings.api_v1_prefix}/suppliers")
        assert response.status_code == 200
        data = response.json()

        # Verify they are sorted alphabetically
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha Industries", "Beta Solutions", "Zebra Corp"]
