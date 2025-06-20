from fastapi.testclient import TestClient


class TestPurposesAPI:
    """Test Purpose API endpoints."""

    def test_get_purposes_empty_list(self, test_client: TestClient):
        """Test GET /purposes returns empty list initially."""
        response = test_client.get("/purposes")
        assert response.status_code == 200
        assert response.json() == {"items": [], "total": 0, "page": 1, "limit": 50}

    def test_create_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test POST /purposes creates new purpose."""
        response = test_client.post("/purposes", json=sample_purpose_data)
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
        response = test_client.post("/purposes", json=invalid_data)
        assert response.status_code == 422

    def test_get_purpose_by_id(
            self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes/{id} returns purpose with EMFs and costs."""
        # Create purpose first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Get purpose by ID
        response = test_client.get(f"/purposes/{purpose_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == purpose_id
        assert data["description"] == sample_purpose_data["description"]
        assert "emfs" in data
        assert isinstance(data["emfs"], list)

    def test_get_purpose_not_found(self, test_client: TestClient):
        """Test GET /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.get("/purposes/999")
        assert response.status_code == 404

    def test_update_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test PUT /purposes/{id} updates purpose."""
        # Create purpose first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Update purpose
        update_data = sample_purpose_data.copy()
        update_data["description"] = "Updated description"
        update_data["status"] = "In Progress"

        response = test_client.put(f"/purposes/{purpose_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["status"] == "In Progress"
        assert data["id"] == purpose_id

    def test_update_purpose_not_found(
            self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test PUT /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.put("/purposes/999", json=sample_purpose_data)
        assert response.status_code == 404

    def test_delete_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test DELETE /purposes/{id} deletes purpose."""
        # Create purpose first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Delete purpose
        response = test_client.delete(f"/purposes/{purpose_id}")
        assert response.status_code == 204

        # Verify purpose is deleted
        get_response = test_client.get(f"/purposes/{purpose_id}")
        assert get_response.status_code == 404

    def test_delete_purpose_not_found(self, test_client: TestClient):
        """Test DELETE /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.delete("/purposes/999")
        assert response.status_code == 404

    def test_get_purposes_with_pagination(
            self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with pagination parameters."""
        # Create multiple purposes
        for i in range(5):
            data = sample_purpose_data.copy()
            data["description"] = f"Purpose {i}"
            test_client.post("/purposes", json=data)

        # Test pagination
        response = test_client.get("/purposes?page=1&limit=2")
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
        # Create purposes with different attributes
        data1 = sample_purpose_data.copy()
        data1["status"] = "Pending"
        data1["supplier"] = "Supplier A"
        test_client.post("/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["status"] = "Completed"
        data2["supplier"] = "Supplier B"
        test_client.post("/purposes", json=data2)

        # Test status filter
        response = test_client.get("/purposes?status=Pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "Pending"

        # Test supplier filter
        response = test_client.get("/purposes?supplier=Supplier B")
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
        test_client.post("/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["description"] = "Hardware procurement"
        data2["content"] = "Buying computers"
        test_client.post("/purposes", json=data2)

        # Test search in description
        response = test_client.get("/purposes?search=software")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["description"].lower()

        # Test search in content
        response = test_client.get("/purposes?search=computers")
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
        data1["excepted_delivery"] = "2024-01-01"
        test_client.post("/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["excepted_delivery"] = "2024-06-01"
        test_client.post("/purposes", json=data2)

        # Test sort by excepted_delivery ascending
        response = test_client.get("/purposes?sort_by=excepted_delivery&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
                data["items"][0]["excepted_delivery"]
                <= data["items"][1]["excepted_delivery"]
        )

        # Test sort by excepted_delivery descending
        response = test_client.get(
            "/purposes?sort_by=excepted_delivery&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
                data["items"][0]["excepted_delivery"]
                >= data["items"][1]["excepted_delivery"]
        )

    def test_get_purposes_combined_filters(
            self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with combined filters, search, and sorting."""
        # Create multiple purposes
        for i in range(3):
            data = sample_purpose_data.copy()
            data["description"] = f"Project {i}"
            data["status"] = "Pending" if i % 2 == 0 else "Completed"
            data["excepted_delivery"] = f"2024-0{i + 1}-01"
            test_client.post("/purposes", json=data)

        # Test combined filters
        response = test_client.get(
            "/purposes?status=Pending&search=Project&sort_by=excepted_delivery&sort_order=desc&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Only pending projects
        for item in data["items"]:
            assert item["status"] == "Pending"
            assert "Project" in item["description"]
