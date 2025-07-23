"""Purpose-specific test fixtures."""

import pytest

from app import Purpose
from app.config import settings
from app.purposes.models import StatusEnum


# Purpose fixtures
@pytest.fixture
def sample_purpose_data(sample_hierarchy) -> dict:
    """Sample purpose data for creation with required fields."""
    return {
        "hierarchy_id": sample_hierarchy.id,
        "expected_delivery": "2024-12-31",
        "comments": "Test comments",
        "status": StatusEnum.IN_PROGRESS.value,
        "description": "Test description",
        "contents": [],  # Empty contents for basic test data
    }


@pytest.fixture
def minimal_purpose_data() -> dict:
    """Minimal purpose data with nullable fields as None."""
    return {
        "status": StatusEnum.IN_PROGRESS.value,
    }


@pytest.fixture
def purpose_data_no_hierarchy() -> dict:
    """Purpose data without hierarchy_id."""
    return {
        "expected_delivery": "2024-12-31",
        "status": StatusEnum.IN_PROGRESS.value,
        "description": "Test description",
        "contents": [],
    }


@pytest.fixture
def purpose_data_no_delivery(sample_hierarchy) -> dict:
    """Purpose data without expected_delivery."""
    return {
        "hierarchy_id": sample_hierarchy.id,
        "status": StatusEnum.IN_PROGRESS.value,
        "description": "Test description",
        "contents": [],
    }


@pytest.fixture
def sample_purpose(db_session, sample_hierarchy) -> Purpose:
    """Create sample purpose with all fields."""
    from datetime import date

    purpose = Purpose(
        hierarchy_id=sample_hierarchy.id,
        expected_delivery=date(2024, 12, 31),
        comments="Test comments",
        status=StatusEnum.IN_PROGRESS,
        description="Test description",
    )
    db_session.add(purpose)
    db_session.commit()
    db_session.refresh(purpose)
    return purpose


@pytest.fixture
def minimal_purpose(db_session) -> Purpose:
    """Create minimal purpose with only required fields."""
    purpose = Purpose(
        status=StatusEnum.IN_PROGRESS,
    )
    db_session.add(purpose)
    db_session.commit()
    db_session.refresh(purpose)
    return purpose


@pytest.fixture
def sample_purpose_data_with_contents(sample_hierarchy, sample_service) -> dict:
    """Sample purpose data with contents for testing."""
    return {
        "hierarchy_id": sample_hierarchy.id,
        "expected_delivery": "2024-12-31",
        "comments": "Test comments",
        "status": StatusEnum.IN_PROGRESS.value,
        "description": "Test description",
        "contents": [{"service_id": sample_service.id, "quantity": 2}],
    }


@pytest.fixture
def created_purpose(test_client, sample_purpose_data):
    """Create a purpose via API and return the response data."""
    response = test_client.post(
        f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def multiple_purposes(test_client, sample_hierarchy):
    """Create multiple purposes for pagination and filtering tests."""
    purposes = []

    base_data = {
        "hierarchy_id": sample_hierarchy.id,
        "expected_delivery": "2024-12-31",
        "status": StatusEnum.IN_PROGRESS.value,
        "contents": [],
    }

    for i in range(8):
        data = base_data.copy()
        data["description"] = f"Purpose {i + 1}"
        data["comments"] = f"Comments for purpose {i + 1}"
        response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=data)
        assert response.status_code == 201
        purposes.append(response.json())

    return purposes


@pytest.fixture
def purpose_with_purchases_and_costs(test_client, sample_hierarchy):
    """Create a purpose with searchable description for testing."""
    purpose_data = {
        "hierarchy_id": sample_hierarchy.id,
        "expected_delivery": "2024-12-31",
        "comments": "Test purpose with searchable content",
        "status": StatusEnum.IN_PROGRESS.value,
        "description": "Complex test purpose with STAGE-001 reference",
        "contents": [],
    }

    response = test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_data)
    assert response.status_code == 201
    return response.json()
