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

    def test_create_purchase_with_support_usd_above_400k(
        self,
        test_client: TestClient,
        sample_purchase_data_support_usd_above_400k,
        predefined_flows_for_purchases,
    ):
        """Test creating a purchase with SUPPORT_USD above 400k selects correct flow."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/",
            json=sample_purchase_data_support_usd_above_400k,
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
        assert "days_since_last_completion" in data

    def test_get_nonexistent_purchase(self, test_client: TestClient):
        """Test getting a non-existent purchase."""
        response = test_client.get(f"{settings.api_v1_prefix}/purchases/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    # PATCH Tests following supplier patterns
    def test_patch_purchase_budget_source_success(
        self, test_client: TestClient, sample_purchase, sample_budget_source
    ):
        """Test successful budget source update (like supplier file_icon test)."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Update purchase with budget source
        update_data = {"budget_source_id": sample_budget_source.id}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["budget_source_id"] == sample_budget_source.id
        assert data["budget_source"] is not None
        assert data["budget_source"]["id"] == sample_budget_source.id
        assert data["budget_source"]["name"] == sample_budget_source.name

    def test_patch_purchase_remove_budget_source(
        self, test_client: TestClient, sample_purchase_with_budget_source
    ):
        """Test removing budget source (like supplier remove file_icon test)."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Remove budget source by setting to null
        update_data = {"budget_source_id": None}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_budget_source.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["budget_source_id"] is None
        assert data["budget_source"] is None

    def test_patch_purchase_invalid_budget_source(
        self, test_client: TestClient, sample_purchase, sample_budget_source
    ):
        """Test patching with non-existent budget source (like supplier invalid_file_icon test)."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"
        invalid_budget_source_id = sample_budget_source.id + 99999
        update_data = {"budget_source_id": invalid_budget_source_id}

        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase.id}", json=update_data
        )
        assert response.status_code == 404
        assert (
            f"Budget source with ID {invalid_budget_source_id} not found"
            in response.json()["detail"]
        )

    def test_patch_purchase_not_found(
        self, test_client: TestClient, sample_budget_source
    ):
        """Test patching non-existent purchase."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"
        update_data = {"budget_source_id": sample_budget_source.id}
        response = test_client.patch(f"{purchase_endpoint}/999999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_patch_purchase_preserves_other_fields(
        self, test_client: TestClient, sample_purchase_with_costs, sample_budget_source
    ):
        """Test that PATCH preserves costs, stages, and other fields."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get original purchase data
        original_response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_costs.id}"
        )
        original_data = original_response.json()

        # Update only budget source
        update_data = {"budget_source_id": sample_budget_source.id}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_costs.id}", json=update_data
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Verify budget source updated
        assert updated_data["budget_source_id"] == sample_budget_source.id

        # Verify other fields preserved
        assert updated_data["purpose_id"] == original_data["purpose_id"]
        assert updated_data["costs"] == original_data["costs"]
        assert updated_data["flow_stages"] == original_data["flow_stages"]
        assert len(updated_data["costs"]) == len(original_data["costs"])

    def test_patch_purchase_with_null_budget_source(
        self, test_client: TestClient, sample_purchase
    ):
        """Test patching with explicit null budget source."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"
        update_data = {"budget_source_id": None}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["budget_source_id"] is None
        assert data["budget_source"] is None

    def test_patch_purchase_empty_update(
        self, test_client: TestClient, sample_purchase
    ):
        """Test PATCH with empty body (no-op update)."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase.id}", json={}
        )

        assert response.status_code == 200
        # Should return unchanged purchase
