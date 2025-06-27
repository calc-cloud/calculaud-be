"""Test Hierarchy CRUD operations using base test mixins."""

from fastapi.testclient import TestClient

from app.config import settings
from tests.base import BaseAPITestClass
from tests.utils import APITestHelper, assert_validation_error


class TestHierarchiesApi(BaseAPITestClass):
    """Test Hierarchy CRUD operations using base test mixins."""

    # Configuration for base test mixins
    resource_name = "hierarchies"
    resource_endpoint = f"{settings.api_v1_prefix}/hierarchies"
    create_data_fixture = "sample_hierarchy_data"
    instance_fixture = "sample_hierarchy"
    multiple_instances_fixture = "multiple_hierarchies"
    search_instances_fixture = "multiple_hierarchies"
    search_field = "name"

    def _get_update_data(self) -> dict:
        """Get data for update operations."""
        return {"name": "Updated Hierarchy Name", "type": "UNIT"}

    def test_create_hierarchy_root_node(self, test_client: TestClient):
        """Test creating a root hierarchy node."""
        hierarchy_data = {
            "type": "CENTER",
            "name": "Root Center",
        }

        response = test_client.post(self.resource_endpoint, json=hierarchy_data)
        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Root Center"
        assert data["type"] == "CENTER"
        assert data["parent_id"] is None
        assert data["path"] == "Root Center"
        assert "id" in data

    def test_create_hierarchy_child_node(self, test_client: TestClient):
        """Test creating a child hierarchy node."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create parent first
        parent_data = {"type": "CENTER", "name": "Parent Center"}
        parent = helper.create_resource(parent_data)

        # Create child
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": parent["id"]}
        child = helper.create_resource(child_data)

        assert child["name"] == "Child Unit"
        assert child["type"] == "UNIT"
        assert child["parent_id"] == parent["id"]
        assert child["path"] == "Parent Center / Child Unit"

    def test_create_hierarchy_invalid_parent(self, test_client: TestClient):
        """Test creating hierarchy with invalid parent ID."""
        hierarchy_data = {
            "type": "UNIT",
            "name": "Test Unit",
            "parent_id": 99999,  # Non-existent parent
        }

        response = test_client.post(self.resource_endpoint, json=hierarchy_data)
        assert response.status_code == 400
        assert "parent" in response.json()["detail"].lower()

    def test_create_hierarchy_invalid_type(self, test_client: TestClient):
        """Test creating hierarchy with invalid type."""
        hierarchy_data = {"type": "INVALID_TYPE", "name": "Test Hierarchy"}

        response = test_client.post(self.resource_endpoint, json=hierarchy_data)
        assert_validation_error(response, "type")

    def test_update_hierarchy_basic_fields(self, test_client: TestClient):
        """Test updating hierarchy basic fields."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create hierarchy
        hierarchy_data = {"type": "CENTER", "name": "Original Name"}
        hierarchy = helper.create_resource(hierarchy_data)

        # Update name and type
        update_data = {"name": "Updated Name", "type": "UNIT"}
        updated_hierarchy = helper.update_resource(hierarchy["id"], update_data)

        assert updated_hierarchy["name"] == "Updated Name"
        assert updated_hierarchy["type"] == "UNIT"
        assert updated_hierarchy["path"] == "Updated Name"  # Path should update

    def test_delete_hierarchy_leaf_node(self, test_client: TestClient):
        """Test deleting a hierarchy leaf node."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create parent and child
        parent = helper.create_resource({"type": "CENTER", "name": "Parent"})
        child = helper.create_resource(
            {"type": "UNIT", "name": "Child", "parent_id": parent["id"]}
        )

        # Delete child (leaf node)
        helper.delete_resource(child["id"])

        # Verify child is deleted but parent remains
        parent_response = test_client.get(f"{self.resource_endpoint}/{parent['id']}")
        assert parent_response.status_code == 200

    def test_delete_hierarchy_with_children_fails(self, test_client: TestClient):
        """Test that deleting hierarchy with children fails."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create parent and child
        parent = helper.create_resource({"type": "CENTER", "name": "Parent"})
        helper.create_resource(
            {"type": "UNIT", "name": "Child", "parent_id": parent["id"]}
        )

        # Try to delete parent (should fail)
        response = test_client.delete(f"{self.resource_endpoint}/{parent['id']}")
        assert response.status_code == 400
        assert "children" in response.json()["detail"].lower()

    def test_hierarchy_prevents_circular_references(self, test_client: TestClient):
        """Test that circular references are prevented."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create hierarchy chain: A -> B -> C
        hierarchy_a = helper.create_resource({"type": "CENTER", "name": "A"})
        hierarchy_b = helper.create_resource(
            {"type": "UNIT", "name": "B", "parent_id": hierarchy_a["id"]}
        )
        hierarchy_c = helper.create_resource(
            {"type": "TEAM", "name": "C", "parent_id": hierarchy_b["id"]}
        )

        # Try to make A a child of C (would create circular reference)
        response = test_client.patch(
            f"{self.resource_endpoint}/{hierarchy_a['id']}",
            json={"parent_id": hierarchy_c["id"]},
        )
        assert response.status_code == 400
        assert "circular" in response.json()["detail"].lower()

    def test_hierarchy_types_validation(self, test_client: TestClient):
        """Test hierarchy type validation."""
        valid_types = ["CENTER", "UNIT", "TEAM", "ANAF"]

        for hierarchy_type in valid_types:
            hierarchy_data = {"type": hierarchy_type, "name": f"Test {hierarchy_type}"}
            response = test_client.post(self.resource_endpoint, json=hierarchy_data)
            assert response.status_code == 201
            assert response.json()["type"] == hierarchy_type

        # Test invalid type
        invalid_data = {"type": "INVALID", "name": "Test Invalid"}
        response = test_client.post(self.resource_endpoint, json=invalid_data)
        assert_validation_error(response, "type")

    def test_create_hierarchy_duplicate_name_same_parent(self, test_client: TestClient):
        """Test that duplicate names under same parent are prevented."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create parent
        parent = helper.create_resource({"type": "CENTER", "name": "Parent"})

        # Create first child
        child_data = {
            "type": "UNIT",
            "name": "Duplicate Name",
            "parent_id": parent["id"],
        }
        helper.create_resource(child_data)

        # Try to create second child with same name
        response = test_client.post(self.resource_endpoint, json=child_data)
        assert response.status_code == 400
        assert (
            "duplicate" in response.json()["detail"].lower()
            or "exists" in response.json()["detail"].lower()
        )

    """Test Hierarchy filtering and search functionality."""

    def test_hierarchy_filtering_by_parent_id(
        self, test_client: TestClient, hierarchy_tree
    ):
        """Test filtering hierarchies by parent ID."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        root_id = hierarchy_tree["root"]["id"]

        # Filter by parent_id (should return children)
        response_data = helper.list_resources(parent_id=root_id)
        assert len(response_data["items"]) == len(hierarchy_tree["children"])

        for item in response_data["items"]:
            assert item["parent_id"] == root_id

    def test_hierarchy_search_functionality(self, test_client: TestClient):
        """Test hierarchy search functionality."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create hierarchies with different names
        hierarchies_data = [
            {"type": "CENTER", "name": "Development Center"},
            {"type": "UNIT", "name": "Testing Unit"},
            {"type": "TEAM", "name": "Development Team"},
            {"type": "ANAF", "name": "Quality Assurance"},
        ]

        for data in hierarchies_data:
            helper.create_resource(data)

        # Search for "Development"
        response_data = helper.search_resources("Development")
        assert len(response_data["items"]) == 2
        for item in response_data["items"]:
            assert "development" in item["name"].lower()

        # Search for "Testing"
        response_data = helper.search_resources("Testing")
        assert len(response_data["items"]) == 1
        assert "testing" in response_data["items"][0]["name"].lower()

    def test_hierarchy_sorting(self, test_client: TestClient):
        """Test hierarchy sorting functionality."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Create hierarchies in random order
        names = ["Zebra Unit", "Alpha Center", "Beta Team"]
        for name in names:
            helper.create_resource({"type": "UNIT", "name": name})

        # Test sorting by name (ascending)
        response_data = helper.list_resources(sort_by="name", sort_order="asc")
        returned_names = [item["name"] for item in response_data["items"]]
        assert returned_names == sorted(names)

        # Test sorting by name (descending)
        response_data = helper.list_resources(sort_by="name", sort_order="desc")
        returned_names = [item["name"] for item in response_data["items"]]
        assert returned_names == sorted(names, reverse=True)

    def test_get_hierarchies_includes_all_levels(
        self, test_client: TestClient, deep_hierarchy
    ):
        """Test that getting hierarchies includes all levels."""
        helper = APITestHelper(test_client, self.resource_endpoint)

        # Get all hierarchies
        response_data = helper.list_resources()

        # Should include root, child, and grandchild
        assert len(response_data["items"]) >= 3

        # Verify all levels are present
        hierarchy_names = [item["name"] for item in response_data["items"]]
        assert "Root" in hierarchy_names
        assert "Child" in hierarchy_names
        assert "Grandchild" in hierarchy_names
