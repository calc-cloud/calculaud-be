from fastapi.testclient import TestClient

from app.config import settings


class TestEMFsAPI:
    """Test EMF API endpoints."""

    def test_add_emf_to_purpose(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test POST /purposes/{id}/emfs adds EMF to purpose with costs."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Add EMF to purpose
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["emf_id"] == sample_emf_data["emf_id"]
        assert data["purpose_id"] == purpose_id
        assert data["order_id"] == sample_emf_data["order_id"]
        assert "id" in data
        assert "creation_time" in data
        assert "costs" in data
        assert len(data["costs"]) == 1
        assert data["costs"][0]["currency"] == "ILS"
        assert data["costs"][0]["cost"] == 1000.50

    def test_add_emf_to_nonexistent_purpose(
        self, test_client: TestClient, sample_emf_data: dict
    ):
        """Test POST /purposes/{id}/emfs returns 404 for non-existent purpose."""
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/999/emfs", json=sample_emf_data)
        assert response.status_code == 404

    def test_add_emf_invalid_data(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test POST /purposes/{id}/emfs with invalid data returns 422."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Try to add EMF with invalid data
        invalid_data = {"invalid_field": "value"}
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=invalid_data)
        assert response.status_code == 422

    def test_add_duplicate_emf_id(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test POST /purposes/{id}/emfs with duplicate EMF ID returns 400."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Add EMF
        test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data)

        # Try to add EMF with same EMF ID
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_update_emf(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PUT /emfs/{id} updates EMF data."""
        # Create purpose and EMF first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Update EMF
        update_data = sample_emf_data.copy()
        update_data["order_id"] = "ORD-002"
        update_data["demand_id"] = "DEM-002"

        response = test_client.put(f"{settings.api_v1_prefix}/emfs/{emf_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "ORD-002"
        assert data["demand_id"] == "DEM-002"
        assert data["id"] == emf_id

    def test_update_emf_not_found(self, test_client: TestClient, sample_emf_data: dict):
        """Test PUT /emfs/{id} returns 404 for non-existent EMF."""
        response = test_client.put(f"{settings.api_v1_prefix}/emfs/999", json=sample_emf_data)
        assert response.status_code == 404

    def test_update_emf_invalid_data(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PUT /emfs/{id} with invalid data returns 422."""
        # Create purpose and EMF first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Try to update with invalid data
        invalid_data = {"order_creation_date": "invalid-date-format"}
        response = test_client.put(f"{settings.api_v1_prefix}/emfs/{emf_id}", json=invalid_data)
        assert response.status_code == 422

    def test_delete_emf(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test DELETE /emfs/{id} deletes EMF."""
        # Create purpose and EMF first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Delete EMF
        response = test_client.delete(f"{settings.api_v1_prefix}/emfs/{emf_id}")
        assert response.status_code == 204

        # Verify EMF is deleted by checking purpose details
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        purpose_data = purpose_response.json()
        emf_ids = [emf["id"] for emf in purpose_data["emfs"]]
        assert emf_id not in emf_ids

    def test_delete_emf_not_found(self, test_client: TestClient):
        """Test DELETE /emfs/{id} returns 404 for non-existent EMF."""
        response = test_client.delete(f"{settings.api_v1_prefix}/emfs/999")
        assert response.status_code == 404

    def test_delete_emf_cascades_to_costs(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        sample_emf_data: dict,
    ):
        """Test DELETE /emfs/{id} cascades delete to associated costs."""
        # Create purpose and EMF with costs
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Verify EMF has costs before deletion
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        purpose_data = purpose_response.json()
        emf = next((e for e in purpose_data["emfs"] if e["id"] == emf_id), None)
        assert emf is not None
        assert len(emf["costs"]) == 1

        # Delete EMF
        response = test_client.delete(f"{settings.api_v1_prefix}/emfs/{emf_id}")
        assert response.status_code == 204

        # Verify EMF and costs are deleted
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        purpose_data = purpose_response.json()
        emf_ids = [emf["id"] for emf in purpose_data["emfs"]]
        assert emf_id not in emf_ids

    def test_emf_appears_in_purpose_details(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test that EMF appears in purpose details after creation."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Add EMF to purpose
        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Get purpose details
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert purpose_response.status_code == 200
        purpose_data = purpose_response.json()

        # Verify EMF is included
        assert len(purpose_data["emfs"]) == 1
        assert purpose_data["emfs"][0]["id"] == emf_id
        assert purpose_data["emfs"][0]["emf_id"] == sample_emf_data["emf_id"]

    def test_multiple_emfs_per_purpose(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test adding multiple EMFs to a single purpose."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Add multiple EMFs
        emf_data_1 = sample_emf_data.copy()
        emf_data_1["emf_id"] = "EMF-001"

        emf_data_2 = sample_emf_data.copy()
        emf_data_2["emf_id"] = "EMF-002"

        emf_data_3 = sample_emf_data.copy()
        emf_data_3["emf_id"] = "EMF-003"

        emf1_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data_1
        )
        emf2_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data_2
        )
        emf3_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data_3
        )

        assert emf1_response.status_code == 201
        assert emf2_response.status_code == 201
        assert emf3_response.status_code == 201

        # Get purpose details
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        purpose_data = purpose_response.json()

        # Verify all EMFs are included
        assert len(purpose_data["emfs"]) == 3
        emf_ids = [emf["emf_id"] for emf in purpose_data["emfs"]]
        assert "EMF-001" in emf_ids
        assert "EMF-002" in emf_ids
        assert "EMF-003" in emf_ids

    def test_add_emf_without_costs(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        sample_emf_data_no_costs: dict,
    ):
        """Test POST /purposes/{id}/emfs adds EMF without costs."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Add EMF to purpose without costs
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data_no_costs
        )
        assert response.status_code == 201
        data = response.json()
        assert data["emf_id"] == sample_emf_data_no_costs["emf_id"]
        assert "costs" in data
        assert len(data["costs"]) == 0

    def test_update_emf_with_costs(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        sample_emf_data_no_costs: dict,
    ):
        """Test PUT /emfs/{id} updates EMF with new costs."""
        # Create purpose and EMF first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data_no_costs
        )
        emf_id = emf_response.json()["id"]

        # Update EMF with costs
        update_data = {
            "costs": [
                {"currency": "ILS", "cost": 500.00},
                {"currency": "SUPPORT_USD", "cost": 150.00},
            ]
        }

        response = test_client.put(f"{settings.api_v1_prefix}/emfs/{emf_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["costs"]) == 2

        # Verify costs are included
        currencies = [cost["currency"] for cost in data["costs"]]
        assert "ILS" in currencies
        assert "SUPPORT_USD" in currencies

    def test_update_emf_replace_costs(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test PUT /emfs/{id} replaces existing costs."""
        # Create purpose and EMF with initial costs
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Update EMF with different costs
        update_data = {"costs": [{"currency": "AVAILABLE_USD", "cost": 800.00}]}

        response = test_client.put(f"{settings.api_v1_prefix}/emfs/{emf_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["costs"]) == 1
        assert data["costs"][0]["currency"] == "AVAILABLE_USD"
        assert data["costs"][0]["cost"] == 800.00

    def test_emf_with_multiple_costs(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating EMF with multiple costs."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Create EMF with multiple costs
        emf_data = {
            "emf_id": "EMF-MULTI",
            "order_id": "ORD-MULTI",
            "costs": [
                {"currency": "ILS", "cost": 1000.00},
                {"currency": "SUPPORT_USD", "cost": 300.00},
                {"currency": "AVAILABLE_USD", "cost": 250.00},
            ],
        }

        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 201
        data = response.json()
        assert len(data["costs"]) == 3

        # Verify all currencies are present
        currencies = [cost["currency"] for cost in data["costs"]]
        assert "ILS" in currencies
        assert "SUPPORT_USD" in currencies
        assert "AVAILABLE_USD" in currencies
