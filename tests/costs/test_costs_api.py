from fastapi.testclient import TestClient

from app.config import settings


class TestCostsAPI:
    """Test Cost integration within EMF operations.

    Note: Costs are now managed exclusively through EMF endpoints.
    These tests verify cost behavior through EMF operations.
    """

    def test_cost_validation_through_emf_creation(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
    ):
        """Test cost validation when creating EMF with costs."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Test valid cost creation through EMF
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": 1000.50}],
        }
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 201
        data = response.json()
        assert len(data["costs"]) == 1
        assert data["costs"][0]["currency"] == "ILS"
        assert data["costs"][0]["cost"] == 1000.50

    def test_invalid_cost_currency_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with invalid cost currency returns 422."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Try to create EMF with invalid currency
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "INVALID", "cost": 100.00}],
        }
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 422

    def test_negative_cost_amount_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with negative cost amount returns 422."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Try to create EMF with negative cost
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": -100.00}],
        }
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 422

    def test_missing_cost_fields_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with missing cost fields returns 422."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Try to create EMF with incomplete cost data
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS"}],  # Missing cost field
        }
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 422

    def test_multiple_costs_through_emf_creation(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating EMF with multiple costs."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Create EMF with multiple costs
        emf_data = {
            "emf_id": "EMF-MULTI",
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

    def test_cost_validation_currency_enum_values(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test cost creation validates currency enum values through EMF."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Test valid currencies
        valid_currencies = ["ILS", "SUPPORT_USD", "AVAILABLE_USD"]
        for currency in valid_currencies:
            emf_data = {
                "emf_id": f"EMF-{currency}",
                "costs": [{"currency": currency, "cost": 100.00}],
            }
            response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
            assert response.status_code == 201

    def test_zero_cost_amount_allowed(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that zero cost amount is allowed."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Test zero cost (should be valid)
        emf_data = {"emf_id": "EMF-ZERO", "costs": [{"currency": "ILS", "cost": 0.00}]}
        response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert response.status_code == 201
        data = response.json()
        assert data["costs"][0]["cost"] == 0.00

    def test_costs_appear_in_purpose_details(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that costs appear in purpose details after EMF creation."""
        # Create purpose first
        create_response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data)
        purpose_id = create_response.json()["id"]

        # Create EMF with costs
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": 1000.50}],
        }
        emf_response = test_client.post(f"{settings.api_v1_prefix}/purposes/{purpose_id}/emfs", json=emf_data)
        assert emf_response.status_code == 201

        # Get purpose details
        purpose_response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert purpose_response.status_code == 200
        purpose_data = purpose_response.json()

        # Verify cost is included in EMF
        emf = purpose_data["emfs"][0]
        assert len(emf["costs"]) == 1
        assert emf["costs"][0]["currency"] == "ILS"
        assert emf["costs"][0]["cost"] == 1000.50
