from fastapi.testclient import TestClient

from app.config import settings


class TestEMFsAPI:
    """Test EMF API endpoints."""

    def test_add_emf_to_purpose(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PATCH /purposes/{id} adds EMF to purpose with costs."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Add EMF to purpose using PATCH
        patch_data = {"emfs": [sample_emf_data]}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["emfs"]) == 1
        emf = data["emfs"][0]
        assert emf["emf_id"] == sample_emf_data["emf_id"]
        assert emf["purpose_id"] == purpose_id
        assert emf["order_id"] == sample_emf_data["order_id"]
        assert "id" in emf
        assert "creation_date" in emf
        assert "costs" in emf
        assert len(emf["costs"]) == 1
        assert emf["costs"][0]["currency"] == "ILS"
        assert emf["costs"][0]["amount"] == 1000.50

    def test_add_emf_to_nonexistent_purpose(
        self, test_client: TestClient, sample_emf_data: dict
    ):
        """Test PATCH /purposes/{id} returns 404 for non-existent purpose."""
        patch_data = {"emfs": [sample_emf_data]}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/999", json=patch_data
        )
        assert response.status_code == 404

    def test_update_emf(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PATCH /purposes/{id} updates EMF data."""
        # Create purpose with EMF first
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [sample_emf_data]
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        purpose_id = create_response.json()["id"]
        emf_id = create_response.json()["emfs"][0]["id"]

        # Update EMF via purpose PATCH
        update_emf_data = sample_emf_data.copy()
        update_emf_data["order_id"] = "ORD-002"
        update_emf_data["demand_id"] = "DEM-002"
        patch_data = {"emfs": [update_emf_data]}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        emf = data["emfs"][0]
        assert emf["order_id"] == "ORD-002"
        assert emf["demand_id"] == "DEM-002"
        assert emf["id"] == emf_id

    def test_update_emf_not_found(self, test_client: TestClient, sample_emf_data: dict):
        """Test PATCH /purposes/{id} returns 404 for non-existent purpose."""
        patch_data = {"emfs": [sample_emf_data]}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/999", json=patch_data
        )
        assert response.status_code == 404

    def test_update_emf_invalid_data(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PATCH /purposes/{id} with invalid EMF data returns 422."""
        # Create purpose with EMF first
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [sample_emf_data]
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Try to update with invalid EMF data
        invalid_emf_data = sample_emf_data.copy()
        invalid_emf_data["order_creation_date"] = "invalid-date-format"
        patch_data = {"emfs": [invalid_emf_data]}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 422

    def test_delete_emf(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PATCH /purposes/{id} removes EMF by not including it."""
        # Create purpose with EMF first
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [sample_emf_data]
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Delete EMF by patching purpose with empty EMFs list
        patch_data = {"emfs": []}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 200

        # Verify EMF is deleted
        data = response.json()
        assert len(data["emfs"]) == 0

    def test_emf_appears_in_purpose_details(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test that EMF appears in purpose details after creation."""
        # Create purpose with EMF
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [sample_emf_data]
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        purpose_id = create_response.json()["id"]
        emf_id = create_response.json()["emfs"][0]["id"]

        # Get purpose details
        purpose_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_response.status_code == 200
        purpose_data = purpose_response.json()

        # Verify EMF is included
        assert len(purpose_data["emfs"]) == 1
        assert purpose_data["emfs"][0]["id"] == emf_id
        assert purpose_data["emfs"][0]["emf_id"] == sample_emf_data["emf_id"]

    def test_multiple_emfs_per_purpose(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test creating purpose with multiple EMFs."""
        # Create multiple EMFs
        emf_data_1 = sample_emf_data.copy()
        emf_data_1["emf_id"] = "EMF-001"

        emf_data_2 = sample_emf_data.copy()
        emf_data_2["emf_id"] = "EMF-002"

        emf_data_3 = sample_emf_data.copy()
        emf_data_3["emf_id"] = "EMF-003"

        # Create purpose with multiple EMFs
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data_1, emf_data_2, emf_data_3]
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert create_response.status_code == 201
        data = create_response.json()

        # Verify all EMFs are included
        assert len(data["emfs"]) == 3
        emf_ids = [emf["emf_id"] for emf in data["emfs"]]
        assert "EMF-001" in emf_ids
        assert "EMF-002" in emf_ids
        assert "EMF-003" in emf_ids

    def test_add_emf_without_costs(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        sample_emf_data_no_costs: dict,
    ):
        """Test creating purpose with EMF without costs."""
        # Create purpose with EMF without costs
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [sample_emf_data_no_costs]
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["emfs"]) == 1
        emf = data["emfs"][0]
        assert emf["emf_id"] == sample_emf_data_no_costs["emf_id"]
        assert "costs" in emf
        assert len(emf["costs"]) == 0

    def test_emf_with_multiple_costs(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating purpose with EMF having multiple costs."""
        # Create EMF with multiple costs
        emf_data = {
            "emf_id": "EMF-MULTI",
            "order_id": "ORD-MULTI",
            "costs": [
                {"currency": "ILS", "amount": 1000.00},
                {"currency": "SUPPORT_USD", "amount": 300.00},
                {"currency": "AVAILABLE_USD", "amount": 250.00},
            ],
        }

        # Create purpose with EMF
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["emfs"]) == 1
        emf = data["emfs"][0]
        assert len(emf["costs"]) == 3

        # Verify all currencies are present
        currencies = [cost["currency"] for cost in emf["costs"]]
        assert "ILS" in currencies
        assert "SUPPORT_USD" in currencies
        assert "AVAILABLE_USD" in currencies
