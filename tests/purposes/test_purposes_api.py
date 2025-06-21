from fastapi.testclient import TestClient

from app.config import settings


class TestPurposesAPI:
    """Test Purpose API endpoints."""

    def test_get_purposes_empty_list(self, test_client: TestClient):
        """Test GET /purposes returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/purposes")
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

    def test_create_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test POST /purposes creates new purpose."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["hierarchy_id"] == sample_purpose_data["hierarchy_id"]
        assert data["description"] == sample_purpose_data["description"]
        assert data["status"] == sample_purpose_data["status"]
        assert "id" in data
        assert "creation_time" in data

    def test_create_purpose_invalid_data(self, test_client: TestClient):
        """Test POST /purposes with invalid data returns 422."""
        invalid_data = {"description": "Missing required fields"}
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=invalid_data
        )
        assert response.status_code == 422

    def test_get_purpose_by_id(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes/{id} returns purpose with EMFs and costs."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Get purpose by ID
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == purpose_id
        assert data["description"] == sample_purpose_data["description"]
        assert "emfs" in data
        assert isinstance(data["emfs"], list)

    def test_get_purpose_not_found(self, test_client: TestClient):
        """Test GET /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/999")
        assert response.status_code == 404

    def test_patch_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test PATCH /purposes/{id} patches purpose."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Patch purpose
        patch_data = sample_purpose_data.copy()
        patch_data["description"] = "Patched description"
        patch_data["status"] = "IN_PROGRESS"

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Patched description"
        assert data["status"] == "IN_PROGRESS"
        assert data["id"] == purpose_id

    def test_patch_purpose_not_found(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test PATCH /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/999", json=sample_purpose_data
        )
        assert response.status_code == 404

    def test_delete_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test DELETE /purposes/{id} deletes purpose."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Delete purpose
        response = test_client.delete(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 204

        # Verify purpose is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert get_response.status_code == 404

    def test_delete_purpose_not_found(self, test_client: TestClient):
        """Test DELETE /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.delete(f"{settings.api_v1_prefix}/purposes/999")
        assert response.status_code == 404

    def test_get_purposes_with_pagination(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with pagination parameters."""
        # Create multiple purposes
        for i in range(5):
            data = sample_purpose_data.copy()
            data["description"] = f"Purpose {i}"
            test_client.post(f"{settings.api_v1_prefix}/purposes", json=data)

        # Test pagination
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2

    def test_get_purposes_with_filters(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with filtering."""
        # Create suppliers first
        supplier_a = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier A"}
        )
        supplier_b = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier B"}
        )
        supplier_a_id = supplier_a.json()["id"]
        supplier_b_id = supplier_b.json()["id"]

        # Create purposes with different attributes
        data1 = sample_purpose_data.copy()
        data1["status"] = "PENDING"
        data1["supplier_id"] = supplier_a_id
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["status"] = "COMPLETED"
        data2["supplier_id"] = supplier_b_id
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test status filter
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "PENDING"

        # Test supplier filter
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?supplier_id={supplier_b_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["supplier"] == "Supplier B"

    def test_get_purposes_with_search(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with search functionality."""
        # Create purposes with different descriptions
        data1 = sample_purpose_data.copy()
        data1["description"] = "Software development project"
        data1["content"] = "Building web application"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["description"] = "Hardware procurement"
        data2["content"] = "Buying computers"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test search in description
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=software")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["description"].lower()

        # Test search in content
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?search=computers"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "computers" in data["items"][0]["content"].lower()

    def test_get_purposes_with_sorting(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with sorting."""
        # Create purposes with different dates
        data1 = sample_purpose_data.copy()
        data1["expected_delivery"] = "2024-01-01"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["expected_delivery"] = "2024-06-01"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test sort by expected_delivery ascending
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?sort_by=expected_delivery&sort_order=asc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
            data["items"][0]["expected_delivery"]
            <= data["items"][1]["expected_delivery"]
        )

        # Test sort by expected_delivery descending
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?sort_by=expected_delivery&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
            data["items"][0]["expected_delivery"]
            >= data["items"][1]["expected_delivery"]
        )

    def test_get_purposes_combined_filters(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with combined filters, search, and sorting."""
        # Create multiple purposes
        for i in range(3):
            data = sample_purpose_data.copy()
            data["description"] = f"Project {i}"
            data["status"] = "PENDING" if i % 2 == 0 else "COMPLETED"
            data["expected_delivery"] = f"2024-0{i + 1}-01"
            test_client.post(f"{settings.api_v1_prefix}/purposes", json=data)

        # Test combined filters
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?status=PENDING&search=Project"
            f"&sort_by=expected_delivery&sort_order=desc&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Only pending projects
        for item in data["items"]:
            assert item["status"] == "PENDING"
            assert "Project" in item["description"]
