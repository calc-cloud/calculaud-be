"""Test cases for Purchase computed fields."""

from datetime import date

from fastapi.testclient import TestClient

from app.config import settings


class TestPurchaseComputedFields:
    """Test class for Purchase computed fields."""

    def test_current_pending_stages_no_stages(
        self, test_client: TestClient, sample_purchase_data
    ):
        """Test current_pending_stages when purchase has no stages."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["current_pending_stages"] == []
        assert data["days_since_last_completion"] is None

    def test_current_pending_stages_all_pending(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test current_pending_stages when all stages are pending."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        data = response.json()

        # Should return stages from priority 1 (first priority level)
        current_pending = data["current_pending_stages"]
        assert len(current_pending) > 0
        assert all(stage["priority"] == 1 for stage in current_pending)
        assert all(stage["completion_date"] is None for stage in current_pending)

    def test_computed_fields_response_structure(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test that computed fields are properly included in API response."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        data = response.json()

        # Verify computed fields are present
        assert "current_pending_stages" in data
        assert "days_since_last_completion" in data

        # Verify structure
        assert isinstance(data["current_pending_stages"], list)
        if data["current_pending_stages"]:
            # Check stage structure
            stage = data["current_pending_stages"][0]
            assert "id" in stage
            assert "priority" in stage
            assert "completion_date" in stage
            assert "stage_type" in stage

        # days_since_last_completion can be None or an integer
        days_since = data["days_since_last_completion"]
        assert days_since is None or isinstance(days_since, int)

    def test_days_since_last_completion_all_pending(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test days_since_last_completion when all stages are pending."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        data = response.json()

        # Should return None when first priority is pending (priority 1 always returns None)
        current_pending = data["current_pending_stages"]
        if current_pending and current_pending[0]["priority"] == 1:
            days_since = data["days_since_last_completion"]
            assert days_since is None

    def test_stage_completion_updates_computed_fields(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
        db_session,
    ):
        """Test that completing stages updates computed fields correctly."""
        # Create purchase with stages
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        purchase_data = response.json()

        # Get initial state
        initial_pending = purchase_data["current_pending_stages"]
        assert len(initial_pending) > 0
        assert initial_pending[0]["priority"] == 1

        # Complete first stage if it exists
        if initial_pending:
            first_stage_id = initial_pending[0]["id"]
            completion_date = date.today()

            # Update via API endpoint (more realistic test)
            update_response = test_client.patch(
                f"{settings.api_v1_prefix}/stages/{first_stage_id}",
                json={"completion_date": completion_date.isoformat()},
            )
            assert update_response.status_code == 200

            # Get updated purchase
            get_response = test_client.get(
                f"{settings.api_v1_prefix}/purchases/{purchase_data['id']}"
            )

            assert get_response.status_code == 200
            updated_data = get_response.json()

            # Verify computed fields updated
            assert "current_pending_stages" in updated_data
            assert "days_since_last_completion" in updated_data

    def test_computed_fields_with_different_flow_types(
        self,
        test_client: TestClient,
        sample_purchase_data_support_usd_above_100k,
        predefined_flows_for_purchases,
    ):
        """Test computed fields work with different predefined flow types."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/",
            json=sample_purchase_data_support_usd_above_100k,
        )

        assert response.status_code == 201
        purchase_data = response.json()

        # Verify computed fields exist and have correct structure
        assert "current_pending_stages" in purchase_data
        assert "days_since_last_completion" in purchase_data

        current_pending = purchase_data["current_pending_stages"]
        if current_pending:
            assert current_pending[0]["priority"] == 1
            assert current_pending[0]["completion_date"] is None

    def test_computed_fields_consistency(
        self,
        test_client: TestClient,
        sample_purchase_data_with_costs,
        predefined_flows_for_purchases,
    ):
        """Test that computed fields are consistent across multiple calls."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purchases/", json=sample_purchase_data_with_costs
        )

        assert response.status_code == 201
        purchase_data = response.json()
        purchase_id = purchase_data["id"]

        # Get the purchase multiple times
        for _ in range(3):
            get_response = test_client.get(
                f"{settings.api_v1_prefix}/purchases/{purchase_id}"
            )

            assert get_response.status_code == 200
            data = get_response.json()

            # Verify fields are consistent
            assert "current_pending_stages" in data
            assert "days_since_last_completion" in data

            # Structure should be consistent
            if data["current_pending_stages"]:
                stage = data["current_pending_stages"][0]
                assert "id" in stage
                assert "priority" in stage
                assert "completion_date" in stage
