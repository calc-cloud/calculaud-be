"""Service-specific test fixtures."""

import pytest

from app import Service
from app.config import settings


# Service fixtures
@pytest.fixture
def sample_service_data(sample_service_type) -> dict:
    """Sample service data for creation."""
    return {"name": "Web Development", "service_type_id": sample_service_type.id}


@pytest.fixture
def sample_service(db_session, sample_service_type) -> Service:
    """Create sample service."""
    service = Service(name="Test Service", service_type_id=sample_service_type.id)
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def multiple_services(test_client, sample_service_type):
    """Create multiple services for pagination and search tests."""
    services = [
        {"name": "Web Development", "service_type_id": sample_service_type.id},
        {"name": "Mobile Development", "service_type_id": sample_service_type.id},
        {"name": "API Development", "service_type_id": sample_service_type.id},
        {"name": "Database Design", "service_type_id": sample_service_type.id},
        {"name": "System Architecture", "service_type_id": sample_service_type.id},
        {"name": "Frontend Development", "service_type_id": sample_service_type.id},
        {"name": "Backend Development", "service_type_id": sample_service_type.id},
        {"name": "Testing Services", "service_type_id": sample_service_type.id},
    ]

    created_services = []
    for data in services:
        response = test_client.post(f"{settings.api_v1_prefix}/services", json=data)
        assert response.status_code == 201
        created_services.append(response.json())

    return created_services


@pytest.fixture
def search_services(test_client, sample_service_type):
    """Create services specifically for search functionality tests."""
    services = [
        {"name": "Web Development", "service_type_id": sample_service_type.id},
        {"name": "Mobile Development", "service_type_id": sample_service_type.id},
        {"name": "API Development", "service_type_id": sample_service_type.id},
        {"name": "Frontend Development", "service_type_id": sample_service_type.id},
        {"name": "Backend Development", "service_type_id": sample_service_type.id},
        {"name": "Database Design", "service_type_id": sample_service_type.id},
        {"name": "System Architecture", "service_type_id": sample_service_type.id},
        {"name": "Testing Labs", "service_type_id": sample_service_type.id},
        {"name": "Quality Assurance", "service_type_id": sample_service_type.id},
        {"name": "Performance Testing", "service_type_id": sample_service_type.id},
    ]

    created_services = []
    for data in services:
        response = test_client.post(f"{settings.api_v1_prefix}/services", json=data)
        assert response.status_code == 201
        created_services.append(response.json())

    return created_services


@pytest.fixture
def multiple_service_types_and_services(test_client):
    """Create multiple service types with services for filtering tests."""
    dev_type = test_client.post(
        f"{settings.api_v1_prefix}/service-types", json={"name": "Development"}
    ).json()

    design_type = test_client.post(
        f"{settings.api_v1_prefix}/service-types", json={"name": "Design"}
    ).json()

    dev_services = []
    for name in ["Web Development", "Mobile Development", "API Development"]:
        response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": name, "service_type_id": dev_type["id"]},
        )
        assert response.status_code == 201
        dev_services.append(response.json())

    design_services = []
    for name in ["UI Design", "UX Design"]:
        response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": name, "service_type_id": design_type["id"]},
        )
        assert response.status_code == 201
        design_services.append(response.json())

    return {
        "dev_type": dev_type,
        "design_type": design_type,
        "dev_services": dev_services,
        "design_services": design_services,
    }


@pytest.fixture
def service_type_and_service(test_client):
    """Create a service type and service for testing."""
    service_type_response = test_client.post(
        f"{settings.api_v1_prefix}/service-types", json={"name": "Test Service Type"}
    )
    assert service_type_response.status_code == 201
    service_type_id = service_type_response.json()["id"]

    service_response = test_client.post(
        f"{settings.api_v1_prefix}/services",
        json={"name": "Test Service", "service_type_id": service_type_id},
    )
    assert service_response.status_code == 201

    return {
        "service_type": service_type_response.json(),
        "service": service_response.json(),
    }
