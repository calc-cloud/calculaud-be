from fastapi.testclient import TestClient


class TestCostsAPI:
    """Test Cost API endpoints."""

    def test_add_cost_to_emf(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test POST /emfs/{id}/costs adds cost to EMF."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Add cost to EMF
        response = test_client.post(f"/emfs/{emf_id}/costs", json=sample_cost_data)
        assert response.status_code == 201
        data = response.json()
        assert data["currency"] == sample_cost_data["currency"]
        assert data["cost"] == sample_cost_data["cost"]
        assert data["emf_id"] == emf_id
        assert "id" in data

    def test_add_cost_to_nonexistent_emf(
            self, test_client: TestClient, sample_cost_data: dict
    ):
        """Test POST /emfs/{id}/costs returns 404 for non-existent EMF."""
        response = test_client.post("/emfs/999/costs", json=sample_cost_data)
        assert response.status_code == 404

    def test_add_cost_invalid_data(
            self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test POST /emfs/{id}/costs with invalid data returns 422."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Try to add cost with invalid data
        invalid_data = {"currency": "INVALID", "cost": "not-a-number"}
        response = test_client.post(f"/emfs/{emf_id}/costs", json=invalid_data)
        assert response.status_code == 422

    def test_add_cost_missing_required_fields(
            self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test POST /emfs/{id}/costs with missing required fields returns 422."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Try to add cost with missing fields
        incomplete_data = {"currency": "ILS"}  # Missing cost field
        response = test_client.post(f"/emfs/{emf_id}/costs", json=incomplete_data)
        assert response.status_code == 422

    def test_update_cost(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test PUT /costs/{id} updates cost."""
        # Create purpose, EMF, and cost first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        cost_response = test_client.post(f"/emfs/{emf_id}/costs", json=sample_cost_data)
        cost_id = cost_response.json()["id"]

        # Update cost
        update_data = sample_cost_data.copy()
        update_data["currency"] = "USD"
        update_data["cost"] = 2000.75

        response = test_client.put(f"/costs/{cost_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "USD"
        assert data["cost"] == 2000.75
        assert data["id"] == cost_id

    def test_update_cost_not_found(
            self, test_client: TestClient, sample_cost_data: dict
    ):
        """Test PUT /costs/{id} returns 404 for non-existent cost."""
        response = test_client.put("/costs/999", json=sample_cost_data)
        assert response.status_code == 404

    def test_update_cost_invalid_data(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test PUT /costs/{id} with invalid data returns 422."""
        # Create purpose, EMF, and cost first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        cost_response = test_client.post(f"/emfs/{emf_id}/costs", json=sample_cost_data)
        cost_id = cost_response.json()["id"]

        # Try to update with invalid data
        invalid_data = {"currency": "INVALID_CURRENCY", "cost": -100}
        response = test_client.put(f"/costs/{cost_id}", json=invalid_data)
        assert response.status_code == 422

    def test_delete_cost(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test DELETE /costs/{id} removes cost."""
        # Create purpose, EMF, and cost first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        cost_response = test_client.post(f"/emfs/{emf_id}/costs", json=sample_cost_data)
        cost_id = cost_response.json()["id"]

        # Delete cost
        response = test_client.delete(f"/costs/{cost_id}")
        assert response.status_code == 204

        # Verify cost is deleted by checking purpose details
        purpose_response = test_client.get(f"/purposes/{purpose_id}")
        purpose_data = purpose_response.json()

        # Check that the EMF has no costs
        emf = next((e for e in purpose_data["emfs"] if e["id"] == emf_id), None)
        assert emf is not None
        assert len(emf["costs"]) == 0

    def test_delete_cost_not_found(self, test_client: TestClient):
        """Test DELETE /costs/{id} returns 404 for non-existent cost."""
        response = test_client.delete("/costs/999")
        assert response.status_code == 404

    def test_cost_appears_in_purpose_details(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test that cost appears in purpose details after creation."""
        # Create purpose, EMF, and cost
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        cost_response = test_client.post(f"/emfs/{emf_id}/costs", json=sample_cost_data)
        cost_id = cost_response.json()["id"]

        # Get purpose details
        purpose_response = test_client.get(f"/purposes/{purpose_id}")
        assert purpose_response.status_code == 200
        purpose_data = purpose_response.json()

        # Verify cost is included in EMF
        emf = purpose_data["emfs"][0]
        assert len(emf["costs"]) == 1
        assert emf["costs"][0]["id"] == cost_id
        assert emf["costs"][0]["currency"] == sample_cost_data["currency"]
        assert emf["costs"][0]["cost"] == sample_cost_data["cost"]

    def test_multiple_costs_per_emf(
            self,
            test_client: TestClient,
            sample_purpose_data: dict,
            sample_emf_data: dict,
            sample_cost_data: dict,
    ):
        """Test adding multiple costs to a single EMF."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Add multiple costs
        cost_data_1 = {"currency": "ILS", "cost": 1000.00}
        cost_data_2 = {"currency": "USD", "cost": 250.50}
        cost_data_3 = {"currency": "EUR", "cost": 800.75}

        cost1_response = test_client.post(f"/emfs/{emf_id}/costs", json=cost_data_1)
        cost2_response = test_client.post(f"/emfs/{emf_id}/costs", json=cost_data_2)
        cost3_response = test_client.post(f"/emfs/{emf_id}/costs", json=cost_data_3)

        assert cost1_response.status_code == 201
        assert cost2_response.status_code == 201
        assert cost3_response.status_code == 201

        # Get purpose details
        purpose_response = test_client.get(f"/purposes/{purpose_id}")
        purpose_data = purpose_response.json()

        # Verify all costs are included
        emf = purpose_data["emfs"][0]
        assert len(emf["costs"]) == 3

        currencies = [cost["currency"] for cost in emf["costs"]]
        assert "ILS" in currencies
        assert "USD" in currencies
        assert "EUR" in currencies

    def test_cost_validation_currency_enum(
            self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test cost creation validates currency enum values."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Test valid currencies
        valid_currencies = ["ILS", "USD", "EUR"]
        for currency in valid_currencies:
            cost_data = {"currency": currency, "cost": 100.00}
            response = test_client.post(f"/emfs/{emf_id}/costs", json=cost_data)
            assert response.status_code == 201

        # Test invalid currency
        invalid_cost_data = {"currency": "INVALID", "cost": 100.00}
        response = test_client.post(f"/emfs/{emf_id}/costs", json=invalid_cost_data)
        assert response.status_code == 422

    def test_cost_validation_negative_amount(
            self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test cost creation validates positive amounts."""
        # Create purpose and EMF first
        create_response = test_client.post("/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        emf_response = test_client.post(
            f"/purposes/{purpose_id}/emfs", json=sample_emf_data
        )
        emf_id = emf_response.json()["id"]

        # Test negative cost
        negative_cost_data = {"currency": "ILS", "cost": -100.00}
        response = test_client.post(f"/emfs/{emf_id}/costs", json=negative_cost_data)
        assert response.status_code == 422

        # Test zero cost (should be valid)
        zero_cost_data = {"currency": "ILS", "cost": 0.00}
        response = test_client.post(f"/emfs/{emf_id}/costs", json=zero_cost_data)
        assert response.status_code == 201
