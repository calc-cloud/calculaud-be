from fastapi.testclient import TestClient

from app.config import settings


class TestHierarchiesAPI:
    """Test Hierarchy API endpoints."""

    def test_get_hierarchies_empty(self, test_client: TestClient):
        """Test GET /hierarchies returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_hierarchy_root_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test POST /hierarchies creates new root hierarchy node."""
        response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == sample_hierarchy_data["type"]
        assert data["name"] == sample_hierarchy_data["name"]
        assert data["parent_id"] is None
        assert "id" in data

    def test_create_hierarchy_child_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test POST /hierarchies creates child hierarchy node."""
        # Create parent node first
        parent_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data)
        parent_id = parent_response.json()["id"]

        # Create child node
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": parent_id}
        response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent_id
        assert data["name"] == "Child Unit"
        assert data["type"] == "UNIT"

    def test_create_hierarchy_invalid_parent(self, test_client: TestClient):
        """Test POST /hierarchies with non-existent parent returns 400."""
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": 999}
        response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)
        assert response.status_code == 400
        assert "parent" in response.json()["detail"].lower()

    def test_create_hierarchy_invalid_data(self, test_client: TestClient):
        """Test POST /hierarchies with invalid data returns 422."""
        invalid_data = {"name": 123}  # Missing type, invalid name type
        response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=invalid_data)
        assert response.status_code == 422

    def test_create_hierarchy_invalid_type(self, test_client: TestClient):
        """Test POST /hierarchies with invalid type returns 422."""
        invalid_data = {"type": "invalid_type", "name": "Test Name"}
        response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=invalid_data)
        assert response.status_code == 422

    def test_get_hierarchy_tree_structure(self, test_client: TestClient):
        """Test GET /hierarchies returns proper tree structure."""
        # Create hierarchy tree
        root_data = {"type": "CENTER", "name": "Main Center"}
        root_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=root_data)
        root_id = root_response.json()["id"]

        # Create child nodes
        child1_data = {"type": "UNIT", "name": "Unit 1", "parent_id": root_id}
        child2_data = {"type": "UNIT", "name": "Unit 2", "parent_id": root_id}

        child1_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child1_data)
        child2_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child2_data)

        child1_id = child1_response.json()["id"]
        child2_id = child2_response.json()["id"]

        # Create grandchild
        grandchild_data = {"type": "UNIT", "name": "Sub Unit", "parent_id": child1_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=grandchild_data)

        # Get full hierarchy
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        hierarchies = response.json()

        # Verify structure - should have root nodes at top level
        root_nodes = [h for h in hierarchies if h["parent_id"] is None]
        assert len(root_nodes) == 1
        assert root_nodes[0]["name"] == "Main Center"

        # Verify all nodes are present
        all_ids = [h["id"] for h in hierarchies]
        assert root_id in all_ids
        assert child1_id in all_ids
        assert child2_id in all_ids

    def test_update_hierarchy(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test PUT /hierarchies/{id} updates hierarchy node."""
        # Create hierarchy first
        create_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data)
        hierarchy_id = create_response.json()["id"]

        # Update hierarchy
        update_data = sample_hierarchy_data.copy()
        update_data["name"] = "Updated Name"
        update_data["type"] = "UNIT"

        response = test_client.put(f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["type"] == "UNIT"
        assert data["id"] == hierarchy_id

    def test_update_hierarchy_not_found(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test PUT /hierarchies/{id} returns 404 for non-existent hierarchy."""
        response = test_client.put(f"{settings.api_v1_prefix}/hierarchies/999", json=sample_hierarchy_data)
        assert response.status_code == 404

    def test_update_hierarchy_change_parent(self, test_client: TestClient):
        """Test updating hierarchy node to change parent."""
        # Create multiple nodes
        root1_data = {"type": "CENTER", "name": "Center 1"}
        root2_data = {"type": "CENTER", "name": "Center 2"}

        root1_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=root1_data)
        root2_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=root2_data)

        root1_id = root1_response.json()["id"]
        root2_id = root2_response.json()["id"]

        # Create child under root1
        child_data = {"type": "UNIT", "name": "Mobile Unit", "parent_id": root1_id}
        child_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)
        child_id = child_response.json()["id"]

        # Move child to root2
        update_data = {"type": "UNIT", "name": "Mobile Unit", "parent_id": root2_id}
        response = test_client.put(f"{settings.api_v1_prefix}/hierarchies/{child_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["parent_id"] == root2_id

    def test_delete_hierarchy_leaf_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test DELETE /hierarchies/{id} deletes leaf node."""
        # Create hierarchy
        create_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data)
        hierarchy_id = create_response.json()["id"]

        # Delete hierarchy
        response = test_client.delete(f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}")
        assert response.status_code == 204

        # Verify hierarchy is deleted
        get_response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        hierarchies = get_response.json()
        hierarchy_ids = [h["id"] for h in hierarchies]
        assert hierarchy_id not in hierarchy_ids

    def test_delete_hierarchy_with_children_fails(self, test_client: TestClient):
        """Test DELETE /hierarchies/{id} fails when node has children."""
        # Create parent and child
        parent_data = {"type": "CENTER", "name": "Parent Center"}
        parent_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=parent_data)
        parent_id = parent_response.json()["id"]

        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": parent_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)

        # Try to delete parent
        response = test_client.delete(f"{settings.api_v1_prefix}/hierarchies/{parent_id}")
        assert response.status_code == 400
        assert "children" in response.json()["detail"].lower()

    def test_delete_hierarchy_not_found(self, test_client: TestClient):
        """Test DELETE /hierarchies/{id} returns 404 for non-existent hierarchy."""
        response = test_client.delete(f"{settings.api_v1_prefix}/hierarchies/999")
        assert response.status_code == 404

    def test_hierarchy_prevents_circular_references(self, test_client: TestClient):
        """Test that hierarchy prevents circular parent-child relationships."""
        # Create parent and child
        parent_data = {"type": "CENTER", "name": "Parent"}
        child_data = {"type": "UNIT", "name": "Child"}

        parent_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=parent_data)
        parent_id = parent_response.json()["id"]

        child_data["parent_id"] = parent_id
        child_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)
        child_id = child_response.json()["id"]

        # Try to make parent a child of child (circular reference)
        update_data = {"type": "CENTER", "name": "Parent", "parent_id": child_id}
        response = test_client.put(f"{settings.api_v1_prefix}/hierarchies/{parent_id}", json=update_data)
        assert response.status_code == 400
        assert "circular" in response.json()["detail"].lower()

    def test_hierarchy_used_in_purposes(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test that hierarchy can be used in purposes."""
        # Create hierarchy
        hierarchy_data = {"type": "UNIT", "name": "Procurement Unit"}
        hierarchy_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data)
        hierarchy_id = hierarchy_response.json()["id"]

        # Create purpose with this hierarchy
        purpose_data = sample_purpose_data.copy()
        purpose_data["hierarchy_id"] = hierarchy_id

        response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_data)
        assert response.status_code == 201
        assert response.json()["hierarchy_id"] == hierarchy_id

    def test_delete_hierarchy_used_in_purposes_fails(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test DELETE /hierarchies/{id} fails when hierarchy is used in purposes."""
        # Create hierarchy
        hierarchy_data = {"type": "UNIT", "name": "Active Unit"}
        hierarchy_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data)
        hierarchy_id = hierarchy_response.json()["id"]

        # Create purpose using this hierarchy
        purpose_data = sample_purpose_data.copy()
        purpose_data["hierarchy_id"] = hierarchy_id
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_data)

        # Try to delete hierarchy
        response = test_client.delete(f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}")
        assert response.status_code == 400
        assert "used" in response.json()["detail"].lower()

    def test_hierarchy_types_validation(self, test_client: TestClient):
        """Test hierarchy creation with different valid types."""
        valid_types = ["UNIT", "CENTER", "ANAF", "TEAM"]

        for hierarchy_type in valid_types:
            data = {"type": hierarchy_type, "name": f"Test {hierarchy_type}"}
            response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=data)
            assert response.status_code == 201
            assert response.json()["type"] == hierarchy_type

    def test_get_hierarchies_includes_all_levels(self, test_client: TestClient):
        """Test GET /hierarchies includes nodes at all hierarchy levels."""
        # Create multi-level hierarchy
        level1_data = {"type": "CENTER", "name": "Level 1"}
        level1_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=level1_data)
        level1_id = level1_response.json()["id"]

        level2_data = {"type": "UNIT", "name": "Level 2", "parent_id": level1_id}
        level2_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=level2_data)
        level2_id = level2_response.json()["id"]

        level3_data = {"type": "UNIT", "name": "Level 3", "parent_id": level2_id}
        level3_response = test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=level3_data)
        level3_id = level3_response.json()["id"]

        # Get all hierarchies
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        hierarchies = response.json()

        # Verify all levels are included
        hierarchy_ids = [h["id"] for h in hierarchies]
        assert level1_id in hierarchy_ids
        assert level2_id in hierarchy_ids
        assert level3_id in hierarchy_ids
        assert len(hierarchy_ids) == 3
