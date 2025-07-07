"""Tests for stage API endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.config import settings


class TestStageAPI:
    """Test stage API endpoints."""

    def test_get_stage_by_id(self, test_client: TestClient, sample_stage):
        """Test getting a stage by ID."""
        response = test_client.get(f"{settings.api_v1_prefix}/stages/{sample_stage.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_stage.id
        assert data["purchase_id"] == sample_stage.purchase_id
        assert data["stage_type_id"] == sample_stage.stage_type_id
        assert data["priority"] == sample_stage.priority
        assert data["value"] == sample_stage.value
        assert data["completion_date"] is None
        assert "stage_type" in data

    def test_get_stage_not_found(self, test_client: TestClient):
        """Test getting a non-existent stage."""
        response = test_client.get(f"{settings.api_v1_prefix}/stages/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_stage_value_only(self, test_client: TestClient, sample_stage):
        """Test updating only the stage value."""
        update_data = {"value": "UPDATED-VALUE-001"}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "UPDATED-VALUE-001"
        assert data["completion_date"] is None  # Should remain unchanged

    def test_update_stage_completion_date_only(
            self, test_client: TestClient, sample_stage
    ):
        """Test updating only the completion date."""
        completion_time = datetime.now().isoformat()
        update_data = {"completion_date": completion_time}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == sample_stage.value  # Should remain unchanged
        assert data["completion_date"] is not None

    def test_update_stage_both_fields(self, test_client: TestClient, sample_stage):
        """Test updating both value and completion date."""
        completion_time = datetime.now().isoformat()
        update_data = {
            "value": "COMPLETED-VALUE-001",
            "completion_date": completion_time,
        }

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "COMPLETED-VALUE-001"
        assert data["completion_date"] is not None

    def test_update_stage_clear_completion_date(
            self, test_client: TestClient, completed_stage
    ):
        """Test clearing the completion date."""
        update_data = {"completion_date": None}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{completed_stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["completion_date"] is None

    def test_update_stage_not_found(self, test_client: TestClient):
        """Test updating a non-existent stage."""
        update_data = {"value": "NEW-VALUE"}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/99999", json=update_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_stage_empty_value_allowed(
            self,
            test_client: TestClient,
            db_session,
            required_value_stage_type,
            sample_purchase,
    ):
        """Test updating stage with empty value is allowed."""
        from app.stages.models import Stage

        # Create stage with required value stage type
        stage = Stage(
            stage_type_id=required_value_stage_type.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value="INITIAL-VALUE",
            completion_date=None,
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        # Update with empty value should work
        update_data = {"value": ""}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == ""

    def test_update_stage_no_value_allowed(
            self,
            test_client: TestClient,
            db_session,
            optional_value_stage_type,
            sample_purchase,
    ):
        """Test updating stage with value when values are not allowed."""
        from app.stages.models import Stage

        # Create stage with stage type that doesn't allow values (value_required=False)
        stage = Stage(
            stage_type_id=optional_value_stage_type.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value=None,  # No initial value
            completion_date=None,
        )
        db_session.add(stage)
        db_session.commit()
        db_session.refresh(stage)

        # Try to update with a value - should fail
        update_data = {"value": "NOT-ALLOWED-VALUE"}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{stage.id}", json=update_data
        )

        assert response.status_code == 400
        assert "values are not allowed" in response.json()["detail"].lower()

    def test_update_stage_partial_update_behavior(
            self, test_client: TestClient, sample_stage
    ):
        """Test that only provided fields are updated (partial update)."""
        original_value = sample_stage.value

        # Update only completion date
        completion_time = datetime.now().isoformat()
        update_data = {"completion_date": completion_time}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == original_value  # Should remain unchanged
        assert data["completion_date"] is not None

    def test_update_stage_invalid_datetime_format(
            self, test_client: TestClient, sample_stage
    ):
        """Test updating stage with invalid datetime format."""
        update_data = {"completion_date": "invalid-datetime"}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json=update_data
        )

        assert response.status_code == 422  # Validation error

    def test_update_stage_empty_request_body(
            self, test_client: TestClient, sample_stage
    ):
        """Test updating stage with empty request body."""
        response = test_client.patch(
            f"{settings.api_v1_prefix}/stages/{sample_stage.id}", json={}
        )

        # Should succeed but not change anything
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == sample_stage.value
        assert data["completion_date"] is None
