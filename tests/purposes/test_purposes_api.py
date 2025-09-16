"""Test Purpose CRUD operations using base test mixins."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.purposes.models import StatusEnum
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper, assert_paginated_response


class TestPurposesApi(BaseAPITestClass):
    """Test Purpose CRUD operations using base test mixins."""

    # Configuration for base test mixins
    resource_name = "purposes"
    resource_endpoint = f"{settings.api_v1_prefix}/purposes"
    create_data_fixture = "sample_purpose_data"
    instance_fixture = "sample_purpose"
    multiple_instances_fixture = "multiple_purposes"
    search_instances_fixture = "multiple_purposes"
    search_field = "description"

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {
            "description": "Updated Purpose Description",
            "status": StatusEnum.IN_PROGRESS.value,
            "comments": "Updated comments",
        }

    def test_create_purpose_response_structure(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that created purpose has correct response structure."""
        response = test_client.post(self.resource_endpoint, json=sample_purpose_data)
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "creation_time" in data
        assert "last_modified" in data
        assert "current_status_changed_at" in data
        assert "hierarchy" in data
        assert "purchases" in data
        assert isinstance(data["purchases"], list)

        # Verify hierarchy relationship is loaded
        if sample_purpose_data.get("hierarchy_id"):
            assert data["hierarchy"]["id"] == sample_purpose_data["hierarchy_id"]

    def test_get_purpose_includes_relationships(
        self, test_client: TestClient, created_purpose
    ):
        """Test that retrieved purpose includes all relationships."""
        response = test_client.get(f"{self.resource_endpoint}/{created_purpose['id']}")
        assert response.status_code == 200
        data = response.json()

        # Verify relationships are loaded
        assert "hierarchy" in data
        assert "purchases" in data
        assert isinstance(data["purchases"], list)

        # Verify timestamp fields are present
        assert "creation_time" in data
        assert "last_modified" in data
        assert "current_status_changed_at" in data

        # Verify response structure matches created purpose
        assert data["id"] == created_purpose["id"]
        assert data["description"] == created_purpose["description"]

    """Test Purpose filtering and search functionality."""

    def test_filter_by_status(
        self, test_client: TestClient, multiple_suppliers_for_filtering
    ):
        """Test filtering purposes by status."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create purposes with different statuses
        base_data = {
            "status": StatusEnum.IN_PROGRESS.value,
            "expected_delivery": "2024-12-31",
        }

        helper.create_resource(
            {
                **base_data,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "In Progress Purpose",
            }
        )
        helper.create_resource(
            {
                **base_data,
                "status": StatusEnum.COMPLETED.value,
                "description": "Completed Purpose",
            }
        )
        helper.create_resource(
            {
                **base_data,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Another In Progress",
            }
        )

        # Test status filter
        response_data = helper.list_resources(status=StatusEnum.IN_PROGRESS.value)
        assert len(response_data["items"]) == 2
        for item in response_data["items"]:
            assert item["status"] == StatusEnum.IN_PROGRESS.value

    def test_filter_by_supplier(
        self, test_client: TestClient, multiple_suppliers_for_filtering
    ):
        """Test filtering purposes by supplier."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        supplier_a_id = multiple_suppliers_for_filtering["supplier_a"]["id"]
        supplier_b_id = multiple_suppliers_for_filtering["supplier_b"]["id"]

        base_data = {
            "status": StatusEnum.IN_PROGRESS.value,
            "expected_delivery": "2024-12-31",
        }

        # Create purposes with different suppliers
        helper.create_resource(
            {**base_data, "supplier_id": supplier_a_id, "description": "Purpose A"}
        )
        helper.create_resource(
            {**base_data, "supplier_id": supplier_b_id, "description": "Purpose B"}
        )
        helper.create_resource(
            {
                **base_data,
                "supplier_id": supplier_a_id,
                "description": "Another Purpose A",
            }
        )

        # Test supplier filter
        response_data = helper.list_resources(supplier_id=supplier_a_id)
        assert len(response_data["items"]) == 2
        for item in response_data["items"]:
            assert item["supplier"] == "Supplier A"

    def test_search_in_description(self, test_client: TestClient, sample_hierarchy):
        """Test searching purposes by description."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        base_data = {
            "hierarchy_id": sample_hierarchy.id,
            "status": StatusEnum.IN_PROGRESS.value,
            "expected_delivery": "2024-12-31",
        }

        # Create purposes with different descriptions
        helper.create_resource(
            {**base_data, "description": "Software development project"}
        )
        helper.create_resource(
            {**base_data, "description": "Hardware procurement for computers"}
        )
        helper.create_resource(
            {**base_data, "description": "Training program for staff"}
        )

        # Test search functionality
        response_data = helper.search_resources("software")
        assert len(response_data["items"]) == 1
        assert "software" in response_data["items"][0]["description"].lower()

        response_data = helper.search_resources("computers")
        assert len(response_data["items"]) == 1
        assert "computers" in response_data["items"][0]["description"].lower()

    def test_search_by_description_content(
        self, test_client: TestClient, purpose_with_purchases_and_costs
    ):
        """Test searching purposes by description content."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Test search by specific content in description
        response_data = helper.search_resources("STAGE-001")
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["id"] == purpose_with_purchases_and_costs["id"]

        # Test search by partial content
        response_data = helper.search_resources("Complex")
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["id"] == purpose_with_purchases_and_costs["id"]

        # Test search by another part of description
        response_data = helper.search_resources("test purpose")
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["id"] == purpose_with_purchases_and_costs["id"]

    def test_sorting_by_expected_delivery(
        self, test_client: TestClient, sample_hierarchy
    ):
        """Test sorting purposes by expected delivery date."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        base_data = {
            "hierarchy_id": sample_hierarchy.id,
            "status": StatusEnum.IN_PROGRESS.value,
            "description": "Test purpose",
        }

        # Create purposes with different delivery dates
        helper.create_resource({**base_data, "expected_delivery": "2024-01-01"})
        helper.create_resource({**base_data, "expected_delivery": "2024-06-01"})
        helper.create_resource({**base_data, "expected_delivery": "2024-03-01"})

        # Test ascending sort
        response_data = helper.list_resources(
            sort_by="expected_delivery", sort_order="asc"
        )
        dates = [item["expected_delivery"] for item in response_data["items"]]
        assert dates == sorted(dates)

        # Test descending sort
        response_data = helper.list_resources(
            sort_by="expected_delivery", sort_order="desc"
        )
        dates = [item["expected_delivery"] for item in response_data["items"]]
        assert dates == sorted(dates, reverse=True)

    def test_combined_filters_search_and_sorting(
        self, test_client: TestClient, sample_hierarchy
    ):
        """Test combining filters, search, and sorting."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        base_data = {
            "hierarchy_id": sample_hierarchy.id,
            "expected_delivery": "2024-12-31",
        }

        # Create multiple purposes with various attributes
        purposes_data = [
            {
                **base_data,
                "description": "Project Alpha",
                "status": StatusEnum.IN_PROGRESS.value,
                "expected_delivery": "2024-03-01",
            },
            {
                **base_data,
                "description": "Project Beta",
                "status": StatusEnum.COMPLETED.value,
                "expected_delivery": "2024-01-01",
            },
            {
                **base_data,
                "description": "Project Gamma",
                "status": StatusEnum.IN_PROGRESS.value,
                "expected_delivery": "2024-05-01",
            },
            {
                **base_data,
                "description": "Task Alpha",
                "status": StatusEnum.IN_PROGRESS.value,
                "expected_delivery": "2024-02-01",
            },
        ]

        for data in purposes_data:
            helper.create_resource(data)

        # Test combined filters: status + search + sorting
        response_data = helper.list_resources(
            status=StatusEnum.IN_PROGRESS.value,
            search="Project",
            sort_by="expected_delivery",
            sort_order="asc",
        )

        assert len(response_data["items"]) == 2  # Only IN_PROGRESS projects
        for item in response_data["items"]:
            assert item["status"] == StatusEnum.IN_PROGRESS.value
            assert "Project" in item["description"]

        # Verify sorting
        dates = [item["expected_delivery"] for item in response_data["items"]]
        assert dates == sorted(dates)

    def test_hierarchy_path_filtering(self, test_client: TestClient, hierarchy_tree):
        """Test filtering purposes by hierarchy path."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        root_id = hierarchy_tree["root"]["id"]
        child1_id = hierarchy_tree["children"][0]["id"]
        child2_id = hierarchy_tree["children"][1]["id"]

        base_data = {
            "status": StatusEnum.IN_PROGRESS.value,
            "expected_delivery": "2024-12-31",
        }

        # Create purposes for different hierarchy levels
        helper.create_resource(
            {**base_data, "hierarchy_id": root_id, "description": "Root Purpose"}
        )
        helper.create_resource(
            {**base_data, "hierarchy_id": child1_id, "description": "Child 1 Purpose"}
        )
        helper.create_resource(
            {**base_data, "hierarchy_id": child2_id, "description": "Child 2 Purpose"}
        )

        # Test filtering by root hierarchy - should return all purposes
        response_data = helper.list_resources(hierarchy_id=root_id)
        assert len(response_data["items"]) == 3

        # Test filtering by child hierarchy - should return only child purposes
        response_data = helper.list_resources(hierarchy_id=child1_id)
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["description"] == "Child 1 Purpose"

    def test_pagination_with_filters(self, test_client: TestClient, multiple_purposes):
        """Test pagination combined with filters."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Test paginated results with filters
        response_data = helper.list_resources(
            status=StatusEnum.IN_PROGRESS.value, page=1, limit=3
        )

        assert_paginated_response(
            response_data,
            expected_total=len(multiple_purposes),
            expected_page=1,
            expected_limit=3,
            expected_has_next=len(multiple_purposes) > 3,
            expected_has_prev=False,
        )

        # Verify all items match filter
        for item in response_data["items"]:
            assert item["status"] == StatusEnum.IN_PROGRESS.value

    def test_filter_by_budget_source_ids(
        self, test_client: TestClient, db_session: Session, sample_hierarchy
    ):
        """Test filtering purposes by budget source IDs through their purchases."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create budget sources
        budget_source_1_response = test_client.post(
            f"{settings.api_v1_prefix}/budget-sources", json={"name": "Budget Source 1"}
        )
        assert budget_source_1_response.status_code == 201
        budget_source_1 = budget_source_1_response.json()

        budget_source_2_response = test_client.post(
            f"{settings.api_v1_prefix}/budget-sources", json={"name": "Budget Source 2"}
        )
        assert budget_source_2_response.status_code == 201
        budget_source_2 = budget_source_2_response.json()

        # Create purposes
        purpose_1_response = helper.create_resource(
            {
                "hierarchy_id": sample_hierarchy.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose with Budget Source 1",
            }
        )

        purpose_2_response = helper.create_resource(
            {
                "hierarchy_id": sample_hierarchy.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose with Budget Source 2",
            }
        )

        purpose_3_response = helper.create_resource(
            {
                "hierarchy_id": sample_hierarchy.id,
                "status": StatusEnum.IN_PROGRESS.value,
                "description": "Purpose without Budget Source",
            }
        )

        # Create purchases with different budget sources
        purchase_1_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases",
            json={
                "purpose_id": purpose_1_response["id"],
                "budget_source_id": budget_source_1["id"],
            },
        )
        assert purchase_1_response.status_code == 201

        purchase_2_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases",
            json={
                "purpose_id": purpose_2_response["id"],
                "budget_source_id": budget_source_2["id"],
            },
        )
        assert purchase_2_response.status_code == 201

        purchase_3_response = test_client.post(
            f"{settings.api_v1_prefix}/purchases",
            json={"purpose_id": purpose_3_response["id"]},
        )
        assert purchase_3_response.status_code == 201

        # Test filtering by single budget source ID
        response_data = helper.list_resources(budget_source_id=budget_source_1["id"])
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["id"] == purpose_1_response["id"]

        # Test filtering by multiple budget source IDs
        response_data = helper.list_resources(
            budget_source_id=[budget_source_1["id"], budget_source_2["id"]]
        )
        assert len(response_data["items"]) == 2
        returned_ids = {item["id"] for item in response_data["items"]}
        expected_ids = {purpose_1_response["id"], purpose_2_response["id"]}
        assert returned_ids == expected_ids

        # Test filtering by non-existent budget source ID
        response_data = helper.list_resources(budget_source_id=999999)
        assert len(response_data["items"]) == 0
