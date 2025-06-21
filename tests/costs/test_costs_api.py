from fastapi.testclient import TestClient

from app.config import settings


class TestCostsAPI:
    """Test Cost integration within EMF operations.

    Note: Costs are now managed exclusively through purpose endpoints.
    These tests verify cost behavior through EMF operations via purpose routes.
    """

    def test_cost_validation_through_emf_creation(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
    ):
        """Test cost validation when creating EMF with costs."""
        # Test valid cost creation through EMF via purpose creation
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": 1000.50}],
        }
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["emfs"]) == 1
        emf = data["emfs"][0]
        assert len(emf["costs"]) == 1
        assert emf["costs"][0]["currency"] == "ILS"
        assert emf["costs"][0]["cost"] == 1000.50

    def test_invalid_cost_currency_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with invalid cost currency returns 422."""
        # Try to create EMF with invalid currency via purpose creation
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "INVALID", "cost": 100.00}],
        }
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 422

    def test_negative_cost_amount_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with negative cost amount returns 422."""
        # Try to create EMF with negative cost via purpose creation
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": -100.00}],
        }
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 422

    def test_missing_cost_fields_in_emf(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test EMF creation with missing cost fields returns 422."""
        # Try to create EMF with incomplete cost data via purpose creation
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS"}],  # Missing cost field
        }
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 422

    def test_multiple_costs_through_emf_creation(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating EMF with multiple costs."""
        # Create EMF with multiple costs via purpose creation
        emf_data = {
            "emf_id": "EMF-MULTI",
            "costs": [
                {"currency": "ILS", "cost": 1000.00},
                {"currency": "SUPPORT_USD", "cost": 300.00},
                {"currency": "AVAILABLE_USD", "cost": 250.00},
            ],
        }
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

    def test_cost_validation_currency_enum_values(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test cost creation validates currency enum values through EMF."""
        # Test valid currencies via purpose creation
        valid_currencies = ["ILS", "SUPPORT_USD", "AVAILABLE_USD"]
        for currency in valid_currencies:
            emf_data = {
                "emf_id": f"EMF-{currency}",
                "costs": [{"currency": currency, "cost": 100.00}],
            }
            purpose_data = sample_purpose_data.copy()
            purpose_data["emfs"] = [emf_data]
            
            response = test_client.post(
                f"{settings.api_v1_prefix}/purposes", json=purpose_data
            )
            assert response.status_code == 201

    def test_zero_cost_amount_allowed(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that zero cost amount is allowed."""
        # Test zero cost (should be valid) via purpose creation
        emf_data = {"emf_id": "EMF-ZERO", "costs": [{"currency": "ILS", "cost": 0.00}]}
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        emf = data["emfs"][0]
        assert emf["costs"][0]["cost"] == 0.00

    def test_costs_appear_in_purpose_details(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that costs appear in purpose details after EMF creation."""
        # Create purpose with EMF and costs
        emf_data = {
            "emf_id": "EMF-001",
            "costs": [{"currency": "ILS", "cost": 1000.50}],
        }
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [emf_data]
        
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert create_response.status_code == 201
        purpose_id = create_response.json()["id"]

        # Get purpose details
        purpose_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_response.status_code == 200
        purpose_response_data = purpose_response.json()

        # Verify cost is included in EMF
        emf = purpose_response_data["emfs"][0]
        assert len(emf["costs"]) == 1
        assert emf["costs"][0]["currency"] == "ILS"
        assert emf["costs"][0]["cost"] == 1000.50
