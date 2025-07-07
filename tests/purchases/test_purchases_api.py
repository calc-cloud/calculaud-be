"""Test cases for Purchase API endpoints."""

from fastapi.testclient import TestClient

from app.config import settings


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
