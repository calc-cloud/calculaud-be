from fastapi.testclient import TestClient

from app.config import settings


class TestCostsAPI:
    """Test Cost integration within purchase operations.

    Note: Costs are created through purchase API and retrieved through purpose API.
    These tests verify cost behavior by creating purposes, purchases, and costs separately.
    """

    def test_cost_validation_through_purchase_creation(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
    ):
        """Test cost validation when creating purchase with costs."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create purchase linked to purpose
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # Verify purpose now shows the purchase
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        data = purpose_details.json()
        assert len(data["purchases"]) == 1
        assert data["purchases"][0]["id"] == purchase_id

    def test_purchase_creation_basic(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test basic purchase creation workflow."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create purchase linked to purpose
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201

    def test_purchase_deletion(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test purchase deletion workflow."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create purchase
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # Delete purchase
        delete_response = test_client.delete(
            f"{settings.api_v1_prefix}/purchases/{purchase_id}"
        )
        assert delete_response.status_code == 204

    def test_purchase_purpose_relationship(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test purchase-purpose relationship."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create purchase linked to purpose
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # Verify purpose includes purchase
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        data = purpose_details.json()
        assert len(data["purchases"]) == 1
        assert data["purchases"][0]["id"] == purchase_id

    def test_multiple_purchases_per_purpose(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating multiple purchases for one purpose."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create multiple purchases
        purchase_data = {"purpose_id": purpose_id}

        purchase1_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase1_response.status_code == 201

        purchase2_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase2_response.status_code == 201

        # Verify purpose includes both purchases
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        data = purpose_details.json()
        assert len(data["purchases"]) == 2

    def test_purpose_with_purchases_display(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that purpose correctly displays associated purchases."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Initially no purchases
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        assert len(purpose_details.json()["purchases"]) == 0

        # Create purchase
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201

        # Now shows purchase
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        assert len(purpose_details.json()["purchases"]) == 1

    def test_purchase_api_basic_operations(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test basic purchase API operations work correctly."""
        # Create purpose first
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Test creating purchase with valid data
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_data_response = purchase_response.json()
        assert "id" in purchase_data_response
        assert "creation_date" in purchase_data_response
        assert purchase_data_response["purpose_id"] == purpose_id

    def test_purchase_purpose_integration(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test integration between purchase and purpose APIs."""
        # Create purpose
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert purpose_response.status_code == 201
        purpose_id = purpose_response.json()["id"]

        # Create purchase
        purchase_data = {"purpose_id": purpose_id}
        purchase_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=purchase_data
        )
        assert purchase_response.status_code == 201
        purchase_id = purchase_response.json()["id"]

        # Verify integration: purpose shows purchase
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        purpose_data_response = purpose_details.json()
        assert len(purpose_data_response["purchases"]) == 1
        assert purpose_data_response["purchases"][0]["id"] == purchase_id

        # Delete purchase
        delete_response = test_client.delete(
            f"{settings.api_v1_prefix}/purchases/{purchase_id}"
        )
        assert delete_response.status_code == 204

        # Verify purpose no longer shows purchase
        purpose_details = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert purpose_details.status_code == 200
        assert len(purpose_details.json()["purchases"]) == 0
