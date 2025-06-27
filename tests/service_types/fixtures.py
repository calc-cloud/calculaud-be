"""Service Type-specific test fixtures."""

import pytest

from app import ServiceType
from app.config import settings


# Service Type fixtures
@pytest.fixture
def sample_service_type_data() -> dict:
    """Sample service type data for creation."""
    return {"name": "Software Development"}


@pytest.fixture
def sample_service_type(db_session) -> ServiceType:
    """Create sample service type."""
    service_type = ServiceType(name="Test Service Type")
    db_session.add(service_type)
    db_session.commit()
    db_session.refresh(service_type)
    return service_type


@pytest.fixture
def multiple_service_types(test_client):
    """Create multiple service types for pagination and search tests."""
    service_types = [
        {"name": "Software Development"},
        {"name": "Hardware Procurement"},
        {"name": "Consulting Services"},
        {"name": "Training Services"},
        {"name": "Maintenance"},
        {"name": "Testing Services"},
        {"name": "Design Services"},
        {"name": "Analysis Services"},
    ]

    created_service_types = []
    for data in service_types:
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=data
        )
        assert response.status_code == 201
        created_service_types.append(response.json())

    return created_service_types


@pytest.fixture
def search_service_types(test_client):
    """Create service types specifically for search functionality tests."""
    service_types = [
        {"name": "Software Development"},
        {"name": "Software Testing"},
        {"name": "Software Consulting"},
        {"name": "Software Design"},
        {"name": "Hardware Procurement"},
        {"name": "Hardware Testing"},
        {"name": "Training Services"},
        {"name": "Consulting Services"},
        {"name": "Development Services"},
        {"name": "Testing Labs"},
    ]

    created_service_types = []
    for data in service_types:
        response = test_client.post(
            f"{settings.api_v1_prefix}/service-types", json=data
        )
        assert response.status_code == 201
        created_service_types.append(response.json())

    return created_service_types
