"""ResponsibleAuthority-specific test fixtures."""

import pytest

from app.config import settings
from app.responsible_authorities.models import ResponsibleAuthority


@pytest.fixture
def sample_responsible_authority_data() -> dict:
    """Sample responsible authority data for creation."""
    return {
        "name": "Finance Department",
        "description": "Department responsible for financial approvals",
    }


@pytest.fixture
def sample_responsible_authority(db_session) -> ResponsibleAuthority:
    """Create sample responsible authority."""
    authority = ResponsibleAuthority(
        name="Test Authority",
        description="Test authority description",
    )
    db_session.add(authority)
    db_session.commit()
    db_session.refresh(authority)
    return authority


@pytest.fixture
def multiple_responsible_authorities(test_client):
    """Create multiple responsible authorities for pagination and search tests."""
    authorities = [
        {
            "name": "Finance Department",
            "description": "Department for financial approvals",
        },
        {
            "name": "Legal Department",
            "description": "Department for legal reviews",
        },
        {
            "name": "Admin Department",
            "description": "Administrative department",
        },
        {
            "name": "HR Department",
            "description": "Human resources department",
        },
        {
            "name": "IT Department",
            "description": "Information technology department",
        },
    ]

    created_authorities = []
    for data in authorities:
        response = test_client.post(
            f"{settings.api_v1_prefix}/responsible-authorities", json=data
        )
        assert response.status_code == 201
        created_authorities.append(response.json())

    return created_authorities


@pytest.fixture
def search_responsible_authorities(test_client):
    """Create responsible authorities specifically for search functionality tests."""
    authorities = [
        {
            "name": "Finance Review",
            "description": "Financial review authority",
        },
        {
            "name": "Finance Approval",
            "description": "Financial approval authority",
        },
        {
            "name": "Legal Review",
            "description": "Legal review authority",
        },
        {
            "name": "Legal Compliance",
            "description": "Legal compliance authority",
        },
        {
            "name": "Admin Support",
            "description": "Administrative support authority",
        },
    ]

    created_authorities = []
    for data in authorities:
        response = test_client.post(
            f"{settings.api_v1_prefix}/responsible-authorities", json=data
        )
        assert response.status_code == 201
        created_authorities.append(response.json())

    return created_authorities
