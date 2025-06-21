from fastapi.testclient import TestClient

from app.config import settings


class TestHierarchiesAPI:
    """Test Hierarchy API endpoints."""

    def test_get_hierarchies_empty(self, test_client: TestClient):
        """Test GET /hierarchies returns empty paginated result initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_create_hierarchy_root_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test POST /hierarchies creates new root hierarchy node."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == sample_hierarchy_data["type"]
        assert data["name"] == sample_hierarchy_data["name"]
        assert data["parent_id"] is None
        assert data["path"] == sample_hierarchy_data["name"]
        assert "id" in data

    def test_create_hierarchy_child_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test POST /hierarchies creates child hierarchy node."""
        # Create parent node first
        parent_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data
        )
        parent_id = parent_response.json()["id"]
        parent_name = parent_response.json()["name"]

        # Create child node
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": parent_id}
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent_id
        assert data["name"] == "Child Unit"
        assert data["type"] == "UNIT"
        assert data["path"] == f"{parent_name} / Child Unit"

    def test_create_hierarchy_deep_nesting(self, test_client: TestClient):
        """Test POST /hierarchies creates deeply nested hierarchy with correct paths."""
        # Create root
        root_data = {"type": "CENTER", "name": "North Unit"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        # Create level 2
        level2_data = {"type": "CENTER", "name": "Tech Center", "parent_id": root_id}
        level2_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=level2_data
        )
        level2_id = level2_response.json()["id"]

        # Create level 3
        level3_data = {"type": "ANAF", "name": "Business ANAF", "parent_id": level2_id}
        level3_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=level3_data
        )

        # Verify paths
        assert root_response.json()["path"] == "North Unit"
        assert level2_response.json()["path"] == "North Unit / Tech Center"
        assert level3_response.json()["path"] == "North Unit / Tech Center / Business ANAF"

    def test_update_hierarchy_path_recalculation(self, test_client: TestClient):
        """Test PATCH /hierarchies/{id} recalculates path when parent changes."""
        # Create hierarchy tree
        root1_data = {"type": "CENTER", "name": "Center 1"}
        root2_data = {"type": "CENTER", "name": "Center 2"}

        root1_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root1_data
        )
        root2_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root2_data
        )

        root1_id = root1_response.json()["id"]
        root2_id = root2_response.json()["id"]

        # Create child under root1
        child_data = {"type": "UNIT", "name": "Mobile Unit", "parent_id": root1_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        # Verify initial path
        assert child_response.json()["path"] == "Center 1 / Mobile Unit"

        # Move child to root2
        update_data = {"parent_id": root2_id}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{child_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == root2_id
        assert response.json()["path"] == "Center 2 / Mobile Unit"

    def test_update_hierarchy_name_path_recalculation(self, test_client: TestClient):
        """Test PATCH /hierarchies/{id} recalculates path when name changes."""
        # Create parent
        parent_data = {"type": "CENTER", "name": "Tech Center"}
        parent_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=parent_data
        )
        parent_id = parent_response.json()["id"]

        # Create child
        child_data = {"type": "UNIT", "name": "Old Name", "parent_id": parent_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        # Verify initial path
        assert child_response.json()["path"] == "Tech Center / Old Name"

        # Update child name
        update_data = {"name": "New Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{child_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        assert response.json()["path"] == "Tech Center / New Name"

    def test_update_hierarchy_children_paths_updated(self, test_client: TestClient):
        """Test PATCH /hierarchies/{id} updates paths for all children when parent path changes."""
        # Create hierarchy tree
        root_data = {"type": "CENTER", "name": "Old Root"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        # Create child
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": root_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        # Create grandchild
        grandchild_data = {"type": "TEAM", "name": "Grandchild Team", "parent_id": child_id}
        grandchild_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=grandchild_data
        )

        # Verify initial paths
        assert child_response.json()["path"] == "Old Root / Child Unit"
        assert grandchild_response.json()["path"] == "Old Root / Child Unit / Grandchild Team"

        # Update root name
        update_data = {"name": "New Root"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{root_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["path"] == "New Root"

        # Verify child and grandchild paths are updated
        child_get_response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/{child_id}")
        grandchild_get_response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/{grandchild_response.json()['id']}")

        assert child_get_response.json()["path"] == "New Root / Child Unit"
        assert grandchild_get_response.json()["path"] == "New Root / Child Unit / Grandchild Team"

    def test_create_hierarchy_invalid_parent(self, test_client: TestClient):
        """Test POST /hierarchies with non-existent parent returns 400."""
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": 999}
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        assert response.status_code == 400
        assert "parent" in response.json()["detail"].lower()

    def test_create_hierarchy_invalid_data(self, test_client: TestClient):
        """Test POST /hierarchies with invalid data returns 422."""
        invalid_data = {"name": 123}  # Missing type, invalid name type
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=invalid_data
        )
        assert response.status_code == 422

    def test_create_hierarchy_invalid_type(self, test_client: TestClient):
        """Test POST /hierarchies with invalid type returns 422."""
        invalid_data = {"type": "invalid_type", "name": "Test Name"}
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=invalid_data
        )
        assert response.status_code == 422

    def test_get_hierarchy_tree_structure(self, test_client: TestClient):
        """Test GET /hierarchies returns proper tree structure."""
        # Create hierarchy tree
        root_data = {"type": "CENTER", "name": "Main Center"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        # Create child nodes
        child1_data = {"type": "UNIT", "name": "Unit 1", "parent_id": root_id}
        child2_data = {"type": "UNIT", "name": "Unit 2", "parent_id": root_id}

        child1_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child1_data
        )
        child2_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child2_data
        )

        child1_id = child1_response.json()["id"]
        child2_id = child2_response.json()["id"]

        # Create grandchild
        grandchild_data = {"type": "UNIT", "name": "Sub Unit", "parent_id": child1_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=grandchild_data)

        # Get full hierarchy
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        data = response.json()
        hierarchies = data["items"]

        # Verify structure - should have root nodes at top level
        root_nodes = [h for h in hierarchies if h["parent_id"] is None]
        assert len(root_nodes) == 1
        assert root_nodes[0]["name"] == "Main Center"
        assert root_nodes[0]["path"] == "Main Center"

        # Verify all nodes are present with correct paths
        all_ids = [h["id"] for h in hierarchies]
        assert root_id in all_ids
        assert child1_id in all_ids
        assert child2_id in all_ids

        # Verify paths
        child1_node = next(h for h in hierarchies if h["id"] == child1_id)
        child2_node = next(h for h in hierarchies if h["id"] == child2_id)
        assert child1_node["path"] == "Main Center / Unit 1"
        assert child2_node["path"] == "Main Center / Unit 2"

    def test_update_hierarchy(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test PATCH /hierarchies/{id} updates hierarchy node."""
        # Create hierarchy first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data
        )
        hierarchy_id = create_response.json()["id"]

        # Update hierarchy
        update_data = {"name": "Updated Name", "type": "UNIT"}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["type"] == "UNIT"
        assert data["id"] == hierarchy_id
        assert data["path"] == "Updated Name"

    def test_update_hierarchy_not_found(self, test_client: TestClient):
        """Test PATCH /hierarchies/{id} returns 404 for non-existent hierarchy."""
        update_data = {"name": "Updated Name"}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/999", json=update_data
        )
        assert response.status_code == 404

    def test_update_hierarchy_change_parent(self, test_client: TestClient):
        """Test updating hierarchy node to change parent."""
        # Create multiple nodes
        root1_data = {"type": "CENTER", "name": "Center 1"}
        root2_data = {"type": "CENTER", "name": "Center 2"}

        root1_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root1_data
        )
        root2_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root2_data
        )

        root1_id = root1_response.json()["id"]
        root2_id = root2_response.json()["id"]

        # Create child under root1
        child_data = {"type": "UNIT", "name": "Mobile Unit", "parent_id": root1_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        # Move child to root2
        update_data = {"parent_id": root2_id}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{child_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == root2_id
        assert response.json()["path"] == "Center 2 / Mobile Unit"

    def test_delete_hierarchy_leaf_node(
        self, test_client: TestClient, sample_hierarchy_data: dict
    ):
        """Test DELETE /hierarchies/{id} deletes leaf node."""
        # Create hierarchy
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=sample_hierarchy_data
        )
        hierarchy_id = create_response.json()["id"]

        # Delete hierarchy
        response = test_client.delete(
            f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}"
        )
        assert response.status_code == 204

        # Verify hierarchy is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}"
        )
        assert get_response.status_code == 404

    def test_delete_hierarchy_with_children_fails(self, test_client: TestClient):
        """Test DELETE /hierarchies/{id} fails when hierarchy has children."""
        # Create parent hierarchy
        parent_data = {"type": "CENTER", "name": "Parent Center"}
        parent_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=parent_data
        )
        parent_id = parent_response.json()["id"]

        # Create child hierarchy
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": parent_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)

        # Try to delete parent
        response = test_client.delete(
            f"{settings.api_v1_prefix}/hierarchies/{parent_id}"
        )
        assert response.status_code == 400
        assert "children" in response.json()["detail"].lower()

    def test_delete_hierarchy_not_found(self, test_client: TestClient):
        """Test DELETE /hierarchies/{id} returns 404 for non-existent hierarchy."""
        response = test_client.delete(f"{settings.api_v1_prefix}/hierarchies/999")
        assert response.status_code == 404

    def test_hierarchy_prevents_circular_references(self, test_client: TestClient):
        """Test hierarchy prevents circular references."""
        # Create hierarchy
        hierarchy_data = {"type": "CENTER", "name": "Test Center"}
        hierarchy_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data
        )
        hierarchy_id = hierarchy_response.json()["id"]

        # Create child
        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": hierarchy_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        # Try to make parent a child of its child
        update_data = {"parent_id": child_id}
        response = test_client.patch(
            f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}", json=update_data
        )
        assert response.status_code == 400
        assert "circular" in response.json()["detail"].lower()

    def test_hierarchy_used_in_purposes(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test hierarchy can be used in purposes."""
        # Create hierarchy
        hierarchy_data = {"type": "CENTER", "name": "Test Center"}
        hierarchy_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data
        )
        hierarchy_id = hierarchy_response.json()["id"]

        # Create purpose with hierarchy
        purpose_data = {**sample_purpose_data, "hierarchy_id": hierarchy_id}
        purpose_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert purpose_response.status_code == 201

    def test_delete_hierarchy_used_in_purposes_fails(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test DELETE /hierarchies/{id} fails when hierarchy is used in purposes."""
        # Create hierarchy
        hierarchy_data = {"type": "CENTER", "name": "Test Center"}
        hierarchy_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data
        )
        hierarchy_id = hierarchy_response.json()["id"]

        # Create purpose with hierarchy
        purpose_data = {**sample_purpose_data, "hierarchy_id": hierarchy_id}
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_data)

        # Try to delete hierarchy
        response = test_client.delete(
            f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}"
        )
        assert response.status_code == 400
        assert "purposes" in response.json()["detail"].lower()

    def test_hierarchy_types_validation(self, test_client: TestClient):
        """Test hierarchy type validation."""
        valid_types = ["UNIT", "CENTER", "ANAF", "TEAM"]
        for hierarchy_type in valid_types:
            data = {"type": hierarchy_type, "name": f"Test {hierarchy_type}"}
            response = test_client.post(
                f"{settings.api_v1_prefix}/hierarchies", json=data
            )
            assert response.status_code == 201

    def test_get_hierarchies_includes_all_levels(self, test_client: TestClient):
        """Test GET /hierarchies includes hierarchies from all levels."""
        # Create multi-level hierarchy
        root_data = {"type": "CENTER", "name": "Root Center"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": root_id}
        child_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        child_id = child_response.json()["id"]

        grandchild_data = {"type": "TEAM", "name": "Grandchild Team", "parent_id": child_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=grandchild_data)

        # Get all hierarchies
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies")
        assert response.status_code == 200
        data = response.json()

        # Should have 3 hierarchies
        assert data["total"] == 3

        # Verify all are present
        hierarchy_ids = [h["id"] for h in data["items"]]
        assert root_id in hierarchy_ids
        assert child_id in hierarchy_ids

        # Verify paths
        root_node = next(h for h in data["items"] if h["id"] == root_id)
        child_node = next(h for h in data["items"] if h["id"] == child_id)
        assert root_node["path"] == "Root Center"
        assert child_node["path"] == "Root Center / Child Unit"

    def test_get_hierarchy_tree_endpoint(self, test_client: TestClient):
        """Test GET /hierarchies/tree returns tree structure."""
        # Create hierarchy tree
        root_data = {"type": "CENTER", "name": "Root Center"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        child_data = {"type": "UNIT", "name": "Child Unit", "parent_id": root_id}
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child_data)

        # Get tree
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/tree")
        assert response.status_code == 200
        data = response.json()

        # Should have root node with children
        assert len(data) == 1
        root_node = data[0]
        assert root_node["name"] == "Root Center"
        assert root_node["path"] == "Root Center"
        assert len(root_node["children"]) == 1
        assert root_node["children"][0]["name"] == "Child Unit"
        assert root_node["children"][0]["path"] == "Root Center / Child Unit"

    def test_get_hierarchy_children_endpoint(self, test_client: TestClient):
        """Test GET /hierarchies/{id}/children returns children."""
        # Create hierarchy with children
        root_data = {"type": "CENTER", "name": "Root Center"}
        root_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=root_data
        )
        root_id = root_response.json()["id"]

        child1_data = {"type": "UNIT", "name": "Child 1", "parent_id": root_id}
        child2_data = {"type": "UNIT", "name": "Child 2", "parent_id": root_id}

        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child1_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child2_data)

        # Get children
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/{root_id}/children")
        assert response.status_code == 200
        data = response.json()

        # Should have 2 children
        assert len(data) == 2
        child_names = [child["name"] for child in data]
        assert "Child 1" in child_names
        assert "Child 2" in child_names

        # Verify paths
        child1 = next(child for child in data if child["name"] == "Child 1")
        child2 = next(child for child in data if child["name"] == "Child 2")
        assert child1["path"] == "Root Center / Child 1"
        assert child2["path"] == "Root Center / Child 2"

    def test_get_hierarchy_by_id_endpoint(self, test_client: TestClient):
        """Test GET /hierarchies/{id} returns specific hierarchy."""
        # Create hierarchy
        hierarchy_data = {"type": "CENTER", "name": "Test Center"}
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=hierarchy_data
        )
        hierarchy_id = create_response.json()["id"]

        # Get hierarchy by ID
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/{hierarchy_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == hierarchy_id
        assert data["name"] == "Test Center"
        assert data["type"] == "CENTER"
        assert data["path"] == "Test Center"

    def test_get_hierarchy_by_id_not_found(self, test_client: TestClient):
        """Test GET /hierarchies/{id} returns 404 for non-existent hierarchy."""
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies/999")
        assert response.status_code == 404

    def test_hierarchy_filtering_by_type(self, test_client: TestClient):
        """Test hierarchy filtering by type."""
        # Create hierarchies of different types
        center_data = {"type": "CENTER", "name": "Test Center"}
        unit_data = {"type": "UNIT", "name": "Test Unit"}
        team_data = {"type": "TEAM", "name": "Test Team"}

        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=center_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=unit_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=team_data)

        # Filter by CENTER type
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies?type=CENTER")
        assert response.status_code == 200
        data = response.json()
        
        # Check that only CENTER types are returned
        center_items = [item for item in data["items"] if item["type"] == "CENTER"]
        assert len(center_items) == 1
        assert center_items[0]["name"] == "Test Center"
        assert center_items[0]["path"] == "Test Center"

    def test_hierarchy_filtering_by_parent_id(self, test_client: TestClient):
        """Test hierarchy filtering by parent_id."""
        # Create parent and children
        parent_data = {"type": "CENTER", "name": "Parent Center"}
        parent_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=parent_data
        )
        parent_id = parent_response.json()["id"]

        child1_data = {"type": "UNIT", "name": "Child 1", "parent_id": parent_id}
        child2_data = {"type": "UNIT", "name": "Child 2", "parent_id": parent_id}

        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child1_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=child2_data)

        # Filter by parent_id
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies?parent_id={parent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        # Verify paths
        for item in data["items"]:
            assert item["parent_id"] == parent_id
            assert item["path"] == f"Parent Center / {item['name']}"

    def test_hierarchy_search_functionality(self, test_client: TestClient):
        """Test hierarchy search functionality."""
        # Create hierarchies with different names
        hierarchy1_data = {"type": "CENTER", "name": "Software Development Center"}
        hierarchy2_data = {"type": "UNIT", "name": "Hardware Unit"}
        hierarchy3_data = {"type": "TEAM", "name": "Testing Team"}

        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy1_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy2_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy3_data)

        # Search for "software"
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies?search=software")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "software" in data["items"][0]["name"].lower()
        assert data["items"][0]["path"] == "Software Development Center"

    def test_hierarchy_sorting(self, test_client: TestClient):
        """Test hierarchy sorting."""
        # Create hierarchies with different names
        hierarchy1_data = {"type": "CENTER", "name": "Zebra Center"}
        hierarchy2_data = {"type": "UNIT", "name": "Alpha Unit"}
        hierarchy3_data = {"type": "TEAM", "name": "Beta Team"}

        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy1_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy2_data)
        test_client.post(f"{settings.api_v1_prefix}/hierarchies", json=hierarchy3_data)

        # Sort by name ascending
        response = test_client.get(f"{settings.api_v1_prefix}/hierarchies?sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha Unit", "Beta Team", "Zebra Center"]

        # Verify paths are included
        for item in data["items"]:
            assert "path" in item
            assert item["path"] == item["name"]

    def test_create_hierarchy_duplicate_name_same_parent(self, test_client: TestClient):
        """Test creating hierarchy with duplicate name under same parent fails."""
        # Create parent
        parent_data = {"type": "CENTER", "name": "Parent Center"}
        parent_response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=parent_data
        )
        parent_id = parent_response.json()["id"]

        # Create first child
        child_data = {"type": "UNIT", "name": "Duplicate Name", "parent_id": parent_id}
        response1 = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies", json=child_data
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
