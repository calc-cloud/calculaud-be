"""Hierarchy-specific test fixtures."""

import pytest

from app import Hierarchy
from app.config import settings


# Hierarchy fixtures
@pytest.fixture
def sample_hierarchy(db_session) -> Hierarchy:
    """Create sample hierarchy."""
    hierarchy = Hierarchy(type="UNIT", name="Test Unit", path="Test Unit")
    db_session.add(hierarchy)
    db_session.commit()
    db_session.refresh(hierarchy)
    return hierarchy


@pytest.fixture
def sample_hierarchy_data() -> dict:
    """Sample hierarchy data for creation."""
    return {"type": "CENTER", "name": "Test Center", "parent_id": None}


@pytest.fixture
def hierarchy_tree(test_client):
    """Create a multi-level hierarchy tree for testing."""
    # Create root
    root_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies",
        json={"type": "CENTER", "name": "Root Center"},
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]

    # Create children
    child1_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies",
        json={"type": "UNIT", "name": "Child Unit 1", "parent_id": root_id},
    )
    assert child1_response.status_code == 201

    child2_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies",
        json={"type": "UNIT", "name": "Child Unit 2", "parent_id": root_id},
    )
    assert child2_response.status_code == 201

    return {
        "root": root_response.json(),
        "children": [child1_response.json(), child2_response.json()],
    }


@pytest.fixture
def deep_hierarchy(test_client):
    """Create a deep hierarchy for path testing."""
    # Create 3-level hierarchy
    root_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies", json={"type": "CENTER", "name": "Root"}
    )
    assert root_response.status_code == 201
    root = root_response.json()

    child_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies",
        json={"type": "UNIT", "name": "Child", "parent_id": root["id"]},
    )
    assert child_response.status_code == 201
    child = child_response.json()

    grandchild_response = test_client.post(
        f"{settings.api_v1_prefix}/hierarchies",
        json={"type": "TEAM", "name": "Grandchild", "parent_id": child["id"]},
    )
    assert grandchild_response.status_code == 201
    grandchild = grandchild_response.json()

    return {"root": root, "child": child, "grandchild": grandchild}


@pytest.fixture
def multiple_hierarchies(test_client):
    """Create multiple hierarchies for pagination and search tests."""
    hierarchies = []

    # Create root hierarchies
    for i in range(5):
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies",
            json={"type": "CENTER", "name": f"Center {i + 1}"},
        )
        assert response.status_code == 201
        hierarchies.append(response.json())

    # Create some child hierarchies
    for i in range(3):
        response = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies",
            json={
                "type": "UNIT",
                "name": f"Unit {i + 1}",
                "parent_id": hierarchies[0]["id"],
            },
        )
        assert response.status_code == 201
        hierarchies.append(response.json())

    return hierarchies
