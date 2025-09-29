"""Test cases for Purchase stage management via PATCH endpoint."""

from fastapi.testclient import TestClient

from app.config import settings


class TestPurchaseStageManagement:
    """Test class for Purchase stage management via PATCH endpoint."""

    def test_patch_purchase_stages_simple_reorder(
        self,
        test_client: TestClient,
        sample_purchase_with_stages,
        stage_types_for_purchases,
    ):
        """Test reordering existing stages with simple array."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get current stages
        response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}"
        )
        original_data = response.json()
        original_stages = [
            s
            for stage_group in original_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]

        # Reorder stages (reverse order for testing)
        stage_edits = [{"id": stage["id"]} for stage in reversed(original_stages)]

        update_data = {"stages": stage_edits}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Verify stages were reordered but data preserved
        updated_stages = [
            s
            for stage_group in updated_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]
        assert len(updated_stages) == len(original_stages)

        # Check that original stage data is preserved
        for i, updated_stage in enumerate(updated_stages):
            original_stage = original_stages[-(i + 1)]  # Reversed order
            assert updated_stage["id"] == original_stage["id"]
            assert updated_stage["value"] == original_stage["value"]
            assert updated_stage["completion_date"] == original_stage["completion_date"]
            assert updated_stage["priority"] == i + 1  # New priority based on position

    def test_patch_purchase_stages_add_new_stage(
        self,
        test_client: TestClient,
        sample_purchase_with_stages,
        stage_types_for_purchases,
    ):
        """Test adding a new stage between existing stages."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get current stages
        response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}"
        )
        original_data = response.json()
        original_stages = [
            s
            for stage_group in original_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]

        # Insert a new stage between first and second existing stages
        stage_edits = [
            {"id": original_stages[0]["id"]},  # Keep first stage
            {"stage_type_id": stage_types_for_purchases[0].id},  # Add new stage
        ] + [
            {"id": stage["id"]} for stage in original_stages[1:]
        ]  # Keep all remaining stages

        update_data = {"stages": stage_edits}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Verify stages count increased
        updated_stages = [
            s
            for stage_group in updated_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]
        assert len(updated_stages) == len(original_stages) + 1

        # Verify priorities are correct
        assert updated_stages[0]["priority"] == 1
        assert updated_stages[1]["priority"] == 2  # New stage
        assert updated_stages[2]["priority"] == 3

        # Verify new stage was created
        assert updated_stages[1]["stage_type_id"] == stage_types_for_purchases[0].id
        assert updated_stages[1]["value"] is None
        assert updated_stages[1]["completion_date"] is None

    def test_patch_purchase_stages_parallel_stages(
        self,
        test_client: TestClient,
        sample_purchase_with_stages,
        stage_types_for_purchases,
    ):
        """Test creating parallel stages at same priority."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get current stages
        response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}"
        )
        original_data = response.json()
        original_stages = [
            s
            for stage_group in original_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]

        # Create structure with parallel stages
        stage_edits = [
            {"id": original_stages[0]["id"]},  # Priority 1: single stage
            [  # Priority 2: parallel stages
                {"id": original_stages[1]["id"]},
                {"stage_type_id": stage_types_for_purchases[0].id},
            ],
            {
                "stage_type_id": stage_types_for_purchases[1].id
            },  # Priority 3: new single stage
        ]

        update_data = {"stages": stage_edits}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Verify flow_stages structure
        flow_stages = updated_data["flow_stages"]
        assert len(flow_stages) == 3  # Three priority levels

        # Priority 1: single stage
        assert isinstance(flow_stages[0], dict)
        assert flow_stages[0]["priority"] == 1

        # Priority 2: parallel stages
        assert isinstance(flow_stages[1], list)
        assert len(flow_stages[1]) == 2
        assert all(stage["priority"] == 2 for stage in flow_stages[1])

        # Priority 3: single stage
        assert isinstance(flow_stages[2], dict)
        assert flow_stages[2]["priority"] == 3

    def test_patch_purchase_stages_preserve_completed_data(
        self, test_client: TestClient, sample_purchase_with_completed_stage
    ):
        """Test that completed stage data is preserved during reordering."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get stage with completion data
        response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_completed_stage.id}"
        )
        original_data = response.json()
        original_stages = [
            s
            for stage_group in original_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]

        # Find the completed stage
        completed_stage = next(
            s for s in original_stages if s["completion_date"] is not None
        )

        # Reorder stages, moving completed stage to different priority
        stage_edits = [{"id": stage["id"]} for stage in reversed(original_stages)]

        update_data = {"stages": stage_edits}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_completed_stage.id}",
            json=update_data,
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Find the completed stage in new structure
        updated_stages = [
            s
            for stage_group in updated_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]
        updated_completed_stage = next(
            s for s in updated_stages if s["id"] == completed_stage["id"]
        )

        # Verify completion data preserved
        assert updated_completed_stage["value"] == completed_stage["value"]
        assert (
            updated_completed_stage["completion_date"]
            == completed_stage["completion_date"]
        )

    def test_patch_purchase_stages_validation_errors(
        self, test_client: TestClient, sample_purchase_with_stages
    ):
        """Test validation errors for stage edits."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Test invalid stage ID
        update_data = {"stages": [{"id": 999999}]}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

        # Test invalid stage type ID
        update_data = {"stages": [{"stage_type_id": 999999}]}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

        # Test stage from different purchase
        # This would need a fixture with another purchase's stage ID

    def test_patch_purchase_stages_remove_stages(
        self, test_client: TestClient, sample_purchase_with_stages
    ):
        """Test removing stages by not including them in the update."""
        purchase_endpoint = f"{settings.api_v1_prefix}/purchases"

        # Get current stages
        response = test_client.get(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}"
        )
        original_data = response.json()
        original_stages = [
            s
            for stage_group in original_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]

        # Keep only first stage, remove others
        stage_edits = [{"id": original_stages[0]["id"]}]

        update_data = {"stages": stage_edits}
        response = test_client.patch(
            f"{purchase_endpoint}/{sample_purchase_with_stages.id}", json=update_data
        )

        assert response.status_code == 200
        updated_data = response.json()

        # Verify only one stage remains
        updated_stages = [
            s
            for stage_group in updated_data["flow_stages"]
            for s in (stage_group if isinstance(stage_group, list) else [stage_group])
        ]
        assert len(updated_stages) == 1
        assert updated_stages[0]["id"] == original_stages[0]["id"]
