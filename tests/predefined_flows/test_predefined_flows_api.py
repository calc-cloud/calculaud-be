from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper


class TestPredefinedFlowsAPI(BaseAPITestClass):
    """Test Predefined Flow API endpoints using base test mixins."""

    # Configuration for base test mixins
    resource_name = "predefined-flows"
    resource_endpoint = f"{settings.api_v1_prefix}/predefined-flows"
    create_data_fixture = "sample_predefined_flow_data"
    instance_fixture = "sample_predefined_flow"
    multiple_instances_fixture = "multiple_predefined_flows"
    search_instances_fixture = "search_predefined_flows"
    search_field = "flow_name"
    required_fields = ["flow_name", "stages"]

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {
            "flow_name": "Updated Flow Name",
            "stages": [1, 2, 3],  # Simplified stage IDs for update
        }

    # All basic CRUD tests are inherited from BaseAPITestClass
    # No need to rewrite test_get_empty_list, test_create_resource, etc.

    def test_create_duplicate_flow_name(
        self, test_client: TestClient, sample_predefined_flow
    ):
        """Test creating a predefined flow with duplicate name returns error."""
        duplicate_data = {
            "flow_name": sample_predefined_flow.flow_name,
            "stages": [1, 2],
        }
        response = test_client.post(self.resource_endpoint, json=duplicate_data)
        assert response.status_code == 409

    def test_predefined_flows_sorted_by_name(
        self, test_client: TestClient, multiple_predefined_flows
    ):
        """Test that predefined flows are returned sorted by name."""
        helper = APITestHelper(test_client, self.resource_endpoint)
        response_data = helper.list_resources()

        names = [item["flow_name"] for item in response_data["items"]]
        expected_names = sorted(
            [flow["flow_name"] for flow in multiple_predefined_flows]
        )
        assert names == expected_names

    def test_create_flow_with_invalid_stage_type(
        self, test_client: TestClient, test_stage_types
    ):
        """Test creating flow with invalid stage type ID returns error."""
        invalid_data = {
            "flow_name": "Invalid Flow",
            "stages": [999999],  # Non-existent stage type ID
        }
        response = test_client.post(self.resource_endpoint, json=invalid_data)
        assert response.status_code == 400
        assert "Stage type with ID 999999 not found" in response.json()["detail"]

    def test_create_flow_with_stage_priorities(
        self, test_client: TestClient, test_stage_types
    ):
        """Test creating flow with different stage priority configurations."""
        stage_ids = [st.id for st in test_stage_types]
        flow_data = {
            "flow_name": "Priority Test Flow",
            "stages": [
                stage_ids[0],  # Single stage priority 1
                [stage_ids[1], stage_ids[2]],  # Multiple stages priority 2
                stage_ids[3],  # Single stage priority 3
            ],
        }
        response = test_client.post(self.resource_endpoint, json=flow_data)
        assert response.status_code == 201

        # Verify flow stages structure
        data = response.json()
        assert "flow_stages" in data
        flow_stages = data["flow_stages"]

        # Should have 3 priority levels
        assert len(flow_stages) == 3

        # First priority should be single stage
        assert isinstance(flow_stages[0], dict)
        assert flow_stages[0]["priority"] == 1

        # Second priority should be list of stages
        assert isinstance(flow_stages[1], list)
        assert len(flow_stages[1]) == 2
        assert all(stage["priority"] == 2 for stage in flow_stages[1])

        # Third priority should be single stage
        assert isinstance(flow_stages[2], dict)
        assert flow_stages[2]["priority"] == 3

    def test_update_flow_stages(
        self, test_client: TestClient, sample_predefined_flow, test_stage_types
    ):
        """Test updating flow stages configuration."""
        stage_ids = [st.id for st in test_stage_types]
        update_data = {
            "stages": [
                [stage_ids[0], stage_ids[1]],  # New priority 1 with multiple stages
                stage_ids[2],  # New priority 2 with single stage
            ]
        }

        response = test_client.patch(
            f"{self.resource_endpoint}/{sample_predefined_flow.id}", json=update_data
        )
        assert response.status_code == 200

        # Verify updated stages
        data = response.json()
        flow_stages = data["flow_stages"]
        assert len(flow_stages) == 2

        # First priority should be list of 2 stages
        assert isinstance(flow_stages[0], list)
        assert len(flow_stages[0]) == 2

        # Second priority should be single stage
        assert isinstance(flow_stages[1], dict)

    def test_flow_stage_type_relationships(
        self, test_client: TestClient, sample_predefined_flow
    ):
        """Test that flow stages include full stage type information."""
        response = test_client.get(
            f"{self.resource_endpoint}/{sample_predefined_flow.id}"
        )
        assert response.status_code == 200

        data = response.json()
        flow_stages = data["flow_stages"]

        # Verify stage type information is included
        for stage_item in flow_stages:
            if isinstance(stage_item, list):
                for stage in stage_item:
                    assert "stage_type" in stage
                    assert "name" in stage["stage_type"]
                    assert "display_name" in stage["stage_type"]
            else:
                assert "stage_type" in stage_item
                assert "name" in stage_item["stage_type"]
                assert "display_name" in stage_item["stage_type"]

    def test_create_flow_with_empty_stages(self, test_client: TestClient):
        """Test creating flow with empty stages list."""
        flow_data = {
            "flow_name": "Empty Flow",
            "stages": [],
        }
        response = test_client.post(self.resource_endpoint, json=flow_data)
        assert response.status_code == 201

        data = response.json()
        assert data["flow_stages"] == []

    def test_update_flow_name_only(
        self, test_client: TestClient, sample_predefined_flow
    ):
        """Test updating only flow name without changing stages."""
        update_data = {"flow_name": "Updated Flow Name Only"}

        response = test_client.patch(
            f"{self.resource_endpoint}/{sample_predefined_flow.id}", json=update_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["flow_name"] == "Updated Flow Name Only"
        # Stages should remain unchanged
        assert len(data["flow_stages"]) > 0

    # New tests for name-based functionality
    def test_create_flow_with_stage_names(
        self, test_client: TestClient, test_stage_types
    ):
        """Test creating a predefined flow using stage names instead of IDs."""
        flow_data = {
            "flow_name": "Name-Based Flow",
            "stages": ["approval", ["review", "validation"], "completion"],
        }
        response = test_client.post(self.resource_endpoint, json=flow_data)
        assert response.status_code == 201

        data = response.json()
        assert data["flow_name"] == "Name-Based Flow"
        # Should have 3 priority levels: approval, [review+validation], completion
        assert len(data["flow_stages"]) == 3

    def test_create_flow_with_mixed_names_and_ids(
        self, test_client: TestClient, test_stage_types
    ):
        """Test creating flow with mix of stage names and IDs."""
        flow_data = {
            "flow_name": "Mixed Format Flow",
            "stages": ["approval", test_stage_types[1].id, "completion"],
        }
        response = test_client.post(self.resource_endpoint, json=flow_data)
        assert response.status_code == 201

        data = response.json()
        assert data["flow_name"] == "Mixed Format Flow"
        assert len(data["flow_stages"]) == 3

    def test_create_flow_with_invalid_stage_name(self, test_client: TestClient):
        """Test creating flow with invalid stage name returns error."""
        flow_data = {
            "flow_name": "Invalid Stage Flow",
            "stages": ["invalid_stage_name", "approval"],
        }
        response = test_client.post(self.resource_endpoint, json=flow_data)
        assert response.status_code == 400

    def test_update_flow_with_stage_names(
        self, test_client: TestClient, sample_predefined_flow
    ):
        """Test updating flow stages using stage names."""
        update_data = {"stages": ["initialization", "approval", "completion"]}
        response = test_client.patch(
            f"{self.resource_endpoint}/{sample_predefined_flow.id}", json=update_data
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["flow_stages"]) == 3

    def test_get_flow_edit_format(
        self, test_client: TestClient, sample_predefined_flow
    ):
        """Test getting flow in edit format returns stage names."""
        response = test_client.get(
            f"{self.resource_endpoint}/{sample_predefined_flow.id}?edit_format=true"
        )
        assert response.status_code == 200

        data = response.json()
        assert "stages" in data
        assert "flow_stages" not in data  # Should not have complex format
        # Should return stage names as strings
        assert all(isinstance(stage, (str, list)) for stage in data["stages"])

    def test_get_flows_edit_format(
        self, test_client: TestClient, multiple_predefined_flows
    ):
        """Test getting flows list in edit format."""
        response = test_client.get(f"{self.resource_endpoint}?edit_format=true")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        # All items should have stages field instead of flow_stages
        for item in data["items"]:
            assert "stages" in item
            assert "flow_stages" not in item
            assert all(isinstance(stage, (str, list)) for stage in item["stages"])
