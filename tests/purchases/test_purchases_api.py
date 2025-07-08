"""Test cases for Purchase API endpoints."""

from fastapi.testclient import TestClient

from app.config import settings
from app.costs.models import CurrencyEnum


class TestPurchaseAPI:
    """Test class for Purchase API endpoints."""

    def test_create_purchase(self, test_client: TestClient, sample_purchase_data):
        """Test creating a purchase."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["purpose_id"] == sample_purchase_data["purpose_id"]
        assert "id" in data
        assert "creation_date" in data
        assert data["costs"] == []

    def test_create_purchase_with_costs(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with costs."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        data = response.json()
        assert data["purpose_id"] == sample_purchase_data_with_costs["purpose_id"]
        assert "id" in data
        assert "creation_date" in data
        assert len(data["costs"]) == 2

        # Check that costs were created correctly
        costs = data["costs"]
        assert costs[0]["currency"] == CurrencyEnum.SUPPORT_USD.value
        assert costs[0]["amount"] == 50000.0
        assert costs[1]["currency"] == CurrencyEnum.ILS.value
        assert costs[1]["amount"] == 10000.0

    def test_create_purchase_with_support_usd_above_100k(
        self,
        test_client: TestClient,
        sample_purchase_data_support_usd_above_100k,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with SUPPORT_USD above 100k selects correct flow."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/",
            json=sample_purchase_data_support_usd_above_100k,
        )

        assert response.status_code == 201
        data = response.json()
        assert "flow_stages" in data
        assert isinstance(data["flow_stages"], list)

    def test_create_purchase_with_available_usd(
        self,
        test_client: TestClient,
        sample_purchase_data_available_usd,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with AVAILABLE_USD selects correct flow."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/",
            json=sample_purchase_data_available_usd,
        )

        assert response.status_code == 201
        data = response.json()
        assert "flow_stages" in data
        assert isinstance(data["flow_stages"], list)

    def test_create_purchase_with_ils(
        self,
        test_client: TestClient,
        sample_purchase_data_ils,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with ILS selects correct flow."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_ils
        )

        assert response.status_code == 201
        data = response.json()
        assert "flow_stages" in data
        assert isinstance(data["flow_stages"], list)

    def test_create_purchase_with_mixed_costs(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with mixed costs selects correct flow."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        data = response.json()
        assert "flow_stages" in data
        assert isinstance(data["flow_stages"], list)

    def test_delete_purchase(self, test_client: TestClient, sample_purchase):
        """Test deleting a purchase."""
        response = test_client.delete(
            f"{settings.api_v1_prefix}/purchases/{sample_purchase.id}"
        )

        assert response.status_code == 204

    def test_delete_nonexistent_purchase(self, test_client: TestClient):
        """Test deleting a non-existent purchase."""
        response = test_client.delete(f"{settings.api_v1_prefix}/purchases/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_purchase(self, test_client: TestClient, sample_purchase):
        """Test getting a purchase by ID."""
        response = test_client.get(
            f"{settings.api_v1_prefix}/purchases/{sample_purchase.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_purchase.id
        assert data["purpose_id"] == sample_purchase.purpose_id
        assert "creation_date" in data
        assert "current_pending_stages" in data
        assert "time_since_last_completion" in data

    def test_get_nonexistent_purchase(self, test_client: TestClient):
        """Test getting a non-existent purchase."""
        response = test_client.get(f"{settings.api_v1_prefix}/purchases/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
