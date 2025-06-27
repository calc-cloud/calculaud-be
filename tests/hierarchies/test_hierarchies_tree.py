"""Test Hierarchy tree operations and path calculations."""

from fastapi.testclient import TestClient

from app.config import settings
from tests.utils import APITestHelper


class TestHierarchyTreeOperations:
    """Test Hierarchy tree-specific operations."""

    def test_create_hierarchy_deep_nesting(self, test_client: TestClient):
        """Test creating deeply nested hierarchy structure."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create 4-level hierarchy
        level1 = helper.create_resource({"type": "CENTER", "name": "Level 1"})
        level2 = helper.create_resource(
            {"type": "UNIT", "name": "Level 2", "parent_id": level1["id"]}
        )
        level3 = helper.create_resource(
            {"type": "TEAM", "name": "Level 3", "parent_id": level2["id"]}
        )
        level4 = helper.create_resource(
            {"type": "ANAF", "name": "Level 4", "parent_id": level3["id"]}
        )

        # Verify paths are calculated correctly
        assert level1["path"] == "Level 1"
        assert level2["path"] == "Level 1 / Level 2"
        assert level3["path"] == "Level 1 / Level 2 / Level 3"
        assert level4["path"] == "Level 1 / Level 2 / Level 3 / Level 4"

    def test_update_hierarchy_path_recalculation(self, test_client: TestClient):
        """Test that updating hierarchy name recalculates paths."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create parent-child relationship
        parent = helper.create_resource({"type": "CENTER", "name": "Original Parent"})
        child = helper.create_resource(
            {"type": "UNIT", "name": "Child", "parent_id": parent["id"]}
        )

        # Verify initial paths
        assert parent["path"] == "Original Parent"
        assert child["path"] == "Original Parent / Child"

        # Update parent name
        updated_parent = helper.update_resource(
            parent["id"], {"name": "Updated Parent"}
        )
        assert updated_parent["path"] == "Updated Parent"

        # Verify child path is updated
        updated_child = helper.get_resource(child["id"])
        assert updated_child["path"] == "Updated Parent / Child"

    def test_update_hierarchy_children_paths_updated(self, test_client: TestClient):
        """Test that updating hierarchy name updates all descendant paths."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create 3-level hierarchy
        root = helper.create_resource({"type": "CENTER", "name": "Root"})
        child = helper.create_resource(
            {"type": "UNIT", "name": "Child", "parent_id": root["id"]}
        )
        grandchild = helper.create_resource(
            {"type": "TEAM", "name": "Grandchild", "parent_id": child["id"]}
        )

        # Update root name
        helper.update_resource(root["id"], {"name": "New Root"})

        # Verify all paths are updated
        updated_root = helper.get_resource(root["id"])
        updated_child = helper.get_resource(child["id"])
        updated_grandchild = helper.get_resource(grandchild["id"])

        assert updated_root["path"] == "New Root"
        assert updated_child["path"] == "New Root / Child"
        assert updated_grandchild["path"] == "New Root / Child / Grandchild"

    def test_update_hierarchy_change_parent(self, test_client: TestClient):
        """Test changing hierarchy parent updates paths correctly."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create structure: Root -> Child1, Root2 -> Child2
        root1 = helper.create_resource({"type": "CENTER", "name": "Root1"})
        root2 = helper.create_resource({"type": "CENTER", "name": "Root2"})
        child1 = helper.create_resource(
            {"type": "UNIT", "name": "Child1", "parent_id": root1["id"]}
        )
        child2 = helper.create_resource(
            {"type": "UNIT", "name": "Child2", "parent_id": root2["id"]}
        )

        # Move Child1 under Root2
        updated_child1 = helper.update_resource(
            child1["id"], {"parent_id": root2["id"]}
        )

        # Verify path is updated
        assert updated_child1["path"] == "Root2 / Child1"
        assert updated_child1["parent_id"] == root2["id"]

        # Verify Child2 path is unchanged
        unchanged_child2 = helper.get_resource(child2["id"])
        assert unchanged_child2["path"] == "Root2 / Child2"

    def test_get_hierarchy_tree_structure(
        self, test_client: TestClient, hierarchy_tree
    ):
        """Test retrieving hierarchy tree structure."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        root_id = hierarchy_tree["root"]["id"]

        # Get root hierarchy with its structure
        root_hierarchy = helper.get_resource(root_id)

        # Verify structure includes hierarchy information
        assert root_hierarchy["id"] == root_id
        assert root_hierarchy["name"] == "Root Center"
        assert root_hierarchy["type"] == "CENTER"
        assert root_hierarchy["parent_id"] is None
        assert root_hierarchy["path"] == "Root Center"

    def test_get_hierarchy_tree_endpoint(self, test_client: TestClient, hierarchy_tree):
        """Test specialized tree endpoint if it exists."""
        # This test assumes there might be a specialized tree endpoint
        # If not, it tests the regular hierarchy listing with tree structure

        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        data = response.json()

        # Should include root and children
        assert len(data["items"]) >= 3  # root + 2 children

        # Find root hierarchy
        root_item = next(
            item for item in data["items"] if item["id"] == hierarchy_tree["root"]["id"]
        )
        assert root_item["parent_id"] is None

        # Find children
        children = [
            item
            for item in data["items"]
            if item["parent_id"] == hierarchy_tree["root"]["id"]
        ]
        assert len(children) == 2

    def test_get_hierarchy_children_endpoint(
        self, test_client: TestClient, hierarchy_tree
    ):
        """Test retrieving hierarchy children."""
        root_id = hierarchy_tree["root"]["id"]

        # Test filtering by parent_id to get children
        response = test_client.get(
            f"{settings.api_v1_prefix}/hierarchies?parent_id={root_id}"
        )
        assert response.status_code == 200
        data = response.json()

        # Should return both children
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["parent_id"] == root_id
            assert item["path"].startswith("Root Center /")

    def test_hierarchy_path_calculations_complex(self, test_client: TestClient):
        """Test complex path calculations with special characters."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create hierarchy with names containing special characters
        parent = helper.create_resource(
            {"type": "CENTER", "name": "Parent-With-Dashes"}
        )
        child = helper.create_resource(
            {"type": "UNIT", "name": "Child With Spaces", "parent_id": parent["id"]}
        )
        grandchild = helper.create_resource(
            {
                "type": "TEAM",
                "name": "Grandchild_With_Underscores",
                "parent_id": child["id"],
            }
        )

        # Verify paths handle special characters correctly
        assert parent["path"] == "Parent-With-Dashes"
        assert child["path"] == "Parent-With-Dashes / Child With Spaces"
        assert (
            grandchild["path"]
            == "Parent-With-Dashes / Child With Spaces / Grandchild_With_Underscores"
        )

    def test_hierarchy_path_uniqueness_validation(self, test_client: TestClient):
        """Test that hierarchy paths maintain uniqueness constraints."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create parent hierarchies
        parent1 = helper.create_resource({"type": "CENTER", "name": "Parent1"})
        parent2 = helper.create_resource({"type": "CENTER", "name": "Parent2"})

        # Create children with same name under different parents (should be allowed)
        child1 = helper.create_resource(
            {"type": "UNIT", "name": "SameName", "parent_id": parent1["id"]}
        )
        child2 = helper.create_resource(
            {"type": "UNIT", "name": "SameName", "parent_id": parent2["id"]}
        )

        # Verify both children exist with different paths
        assert child1["path"] == "Parent1 / SameName"
        assert child2["path"] == "Parent2 / SameName"
        assert child1["id"] != child2["id"]

    def test_hierarchy_tree_depth_limits(self, test_client: TestClient):
        """Test hierarchy tree depth handling."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create very deep hierarchy (test reasonable depth)
        current_parent = helper.create_resource({"type": "CENTER", "name": "Level 0"})

        for i in range(1, 6):  # Create 5 levels deep
            current_parent = helper.create_resource(
                {
                    "type": "UNIT",
                    "name": f"Level {i}",
                    "parent_id": current_parent["id"],
                }
            )

        # Verify final level has correct path
        expected_path = " / ".join([f"Level {i}" for i in range(6)])
        assert current_parent["path"] == expected_path

    def test_hierarchy_move_subtree(self, test_client: TestClient):
        """Test moving an entire subtree to a new parent."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create structure: Root1 -> Branch -> Leaf, Root2
        root1 = helper.create_resource({"type": "CENTER", "name": "Root1"})
        root2 = helper.create_resource({"type": "CENTER", "name": "Root2"})
        branch = helper.create_resource(
            {"type": "UNIT", "name": "Branch", "parent_id": root1["id"]}
        )
        leaf = helper.create_resource(
            {"type": "TEAM", "name": "Leaf", "parent_id": branch["id"]}
        )

        # Move branch (and its subtree) under Root2
        updated_branch = helper.update_resource(
            branch["id"], {"parent_id": root2["id"]}
        )

        # Verify both branch and leaf paths are updated
        assert updated_branch["path"] == "Root2 / Branch"

        updated_leaf = helper.get_resource(leaf["id"])
        assert updated_leaf["path"] == "Root2 / Branch / Leaf"

    def test_hierarchy_root_node_operations(self, test_client: TestClient):
        """Test operations specific to root nodes."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create root node
        root = helper.create_resource({"type": "CENTER", "name": "Root"})

        # Verify root properties
        assert root["parent_id"] is None
        assert root["path"] == "Root"

        # Try to make root a child of itself (should fail)
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{root['id']}",
            json={"parent_id": root["id"]},
        )
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "circular" in detail or "own parent" in detail

    def test_hierarchy_path_consistency_after_operations(self, test_client: TestClient):
        """Test that paths remain consistent after multiple operations."""
        helper = APITestHelper(test_client, f"{settings.api_v1_prefix}/hierarchies")

        # Create initial structure
        root = helper.create_resource({"type": "CENTER", "name": "Root"})
        child1 = helper.create_resource(
            {"type": "UNIT", "name": "Child1", "parent_id": root["id"]}
        )
        child2 = helper.create_resource(
            {"type": "UNIT", "name": "Child2", "parent_id": root["id"]}
        )

        # Perform multiple operations
        # 1. Rename root
        helper.update_resource(root["id"], {"name": "NewRoot"})

        # 2. Move child2 under child1
        helper.update_resource(child2["id"], {"parent_id": child1["id"]})

        # 3. Rename child1
        helper.update_resource(child1["id"], {"name": "RenamedChild1"})

        # Verify final paths are correct
        final_root = helper.get_resource(root["id"])
        final_child1 = helper.get_resource(child1["id"])
        final_child2 = helper.get_resource(child2["id"])

        assert final_root["path"] == "NewRoot"
        assert final_child1["path"] == "NewRoot / RenamedChild1"
        assert final_child2["path"] == "NewRoot / RenamedChild1 / Child2"
