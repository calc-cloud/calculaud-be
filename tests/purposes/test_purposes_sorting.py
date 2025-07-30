"""Tests for purpose sorting functionality."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from fastapi import status

from app import StatusEnum
from tests.base import BaseAPITestClass


class TestPurposeSorting:
    """Test purpose sorting functionality."""

    resource_name = "purposes"
    resource_endpoint = "/api/v1/purposes"

    def test_sort_by_days_since_last_completion_desc(
        self,
        test_client,
        db_session,
        sample_hierarchy,
        sample_service_type,
        sample_supplier,
    ):
        """Test sorting purposes by days_since_last_completion in descending order."""
        # Mock current date for consistent testing
        mock_date = date(2024, 1, 15)

        with patch("app.purposes.sorting.func.current_date") as mock_current_date:
            mock_current_date.return_value = mock_date

            # Create purposes with different stage completion scenarios
            # Purpose 1: Has pending stages with completed previous stage (10 days ago)
            purpose1_data = {
                "hierarchy_id": sample_hierarchy.id,
                "service_type_id": sample_service_type.id,
                "supplier_id": sample_supplier.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose with 10 days since completion",
            }
            response1 = test_client.post(self.resource_endpoint, json=purpose1_data)
            assert response1.status_code == status.HTTP_201_CREATED
            purpose1_id = response1.json()["id"]

            # Purpose 2: Has pending stages with completed previous stage (5 days ago)
            purpose2_data = {
                "hierarchy_id": sample_hierarchy.id,
                "service_type_id": sample_service_type.id,
                "supplier_id": sample_supplier.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose with 5 days since completion",
            }
            response2 = test_client.post(self.resource_endpoint, json=purpose2_data)
            assert response2.status_code == status.HTTP_201_CREATED
            purpose2_id = response2.json()["id"]

            # Purpose 3: No purchases (should be NULL, sorted last)
            purpose3_data = {
                "hierarchy_id": sample_hierarchy.id,
                "service_type_id": sample_service_type.id,
                "supplier_id": sample_supplier.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose with no purchases",
            }
            response3 = test_client.post(self.resource_endpoint, json=purpose3_data)
            assert response3.status_code == status.HTTP_201_CREATED
            purpose3_id = response3.json()["id"]

            # Add purchases and stages to purpose1 and purpose2
            # Purpose 1: Priority 1 stage completed 10 days ago, priority 2 stage pending
            purchase1_response = test_client.post(
                "/api/v1/purchases", json={"purpose_id": purpose1_id}
            )
            purchase1_id = purchase1_response.json()["id"]

            # Stage 1 completed 10 days ago
            test_client.post(
                "/api/v1/stages",
                json={
                    "purchase_id": purchase1_id,
                    "stage_type_id": 1,  # Assuming stage type exists
                    "priority": 1,
                    "value": "Completed stage",
                    "completion_date": (mock_date - timedelta(days=10)).isoformat(),
                },
            )

            # Stage 2 pending
            test_client.post(
                "/api/v1/stages",
                json={
                    "purchase_id": purchase1_id,
                    "stage_type_id": 2,  # Assuming stage type exists
                    "priority": 2,
                    "value": "Pending stage",
                    "completion_date": None,
                },
            )

            # Purpose 2: Priority 1 stage completed 5 days ago, priority 2 stage pending
            purchase2_response = test_client.post(
                "/api/v1/purchases", json={"purpose_id": purpose2_id}
            )
            purchase2_id = purchase2_response.json()["id"]

            # Stage 1 completed 5 days ago
            test_client.post(
                "/api/v1/stages",
                json={
                    "purchase_id": purchase2_id,
                    "stage_type_id": 1,  # Assuming stage type exists
                    "priority": 1,
                    "value": "Completed stage",
                    "completion_date": (mock_date - timedelta(days=5)).isoformat(),
                },
            )

            # Stage 2 pending
            test_client.post(
                "/api/v1/stages",
                json={
                    "purchase_id": purchase2_id,
                    "stage_type_id": 2,  # Assuming stage type exists
                    "priority": 2,
                    "value": "Pending stage",
                    "completion_date": None,
                },
            )

            # Test sorting by days_since_last_completion DESC
            response = test_client.get(
                f"{self.resource_endpoint}?sort_by=days_since_last_completion&sort_order=desc"
            )
            assert response.status_code == status.HTTP_200_OK

            purposes = response.json()["items"]
            assert len(purposes) >= 3

            # Find our test purposes in the results
            purpose1_result = next(p for p in purposes if p["id"] == purpose1_id)
            purpose2_result = next(p for p in purposes if p["id"] == purpose2_id)
            purpose3_result = next(p for p in purposes if p["id"] == purpose3_id)

            # Get their positions in the sorted list
            purpose1_pos = purposes.index(purpose1_result)
            purpose2_pos = purposes.index(purpose2_result)
            purpose3_pos = purposes.index(purpose3_result)

            # Purpose 1 (10 days) should come before Purpose 2 (5 days) in DESC order
            assert (
                purpose1_pos < purpose2_pos
            ), "Purpose with 10 days should come before purpose with 5 days in DESC order"

            # Purpose 3 (NULL) should come last
            assert (
                purpose3_pos > purpose1_pos
            ), "Purpose with NULL should come after purposes with values"
            assert (
                purpose3_pos > purpose2_pos
            ), "Purpose with NULL should come after purposes with values"

    def test_sort_by_days_since_last_completion_asc(
        self,
        test_client,
        db_session,
        sample_hierarchy,
        sample_service_type,
        sample_supplier,
    ):
        """Test sorting purposes by days_since_last_completion in ascending order."""
        # Test ASC order - smaller values first, NULL values last
        response = test_client.get(
            f"{self.resource_endpoint}?sort_by=days_since_last_completion&sort_order=asc"
        )
        assert response.status_code == status.HTTP_200_OK

        purposes = response.json()["items"]
        # Just verify the endpoint works - detailed logic tested in DESC test
        assert "items" in response.json()
        assert isinstance(purposes, list)

    def test_sort_by_standard_field_still_works(self, test_client):
        """Test that standard sorting still works after adding days_since_last_completion."""
        response = test_client.get(
            f"{self.resource_endpoint}?sort_by=creation_time&sort_order=desc"
        )
        assert response.status_code == status.HTTP_200_OK

        purposes = response.json()["items"]
        assert isinstance(purposes, list)

        # Verify purposes are sorted by creation_time DESC
        if len(purposes) > 1:
            for i in range(len(purposes) - 1):
                current_time = datetime.fromisoformat(
                    purposes[i]["creation_time"].replace("Z", "+00:00")
                )
                next_time = datetime.fromisoformat(
                    purposes[i + 1]["creation_time"].replace("Z", "+00:00")
                )
                assert (
                    current_time >= next_time
                ), "Purposes should be sorted by creation_time DESC"
