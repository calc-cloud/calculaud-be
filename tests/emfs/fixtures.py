"""EMF-specific test fixtures."""

from datetime import date

import pytest

from app import EMF


# EMF fixtures
@pytest.fixture
def sample_emf_data() -> dict:
    """Sample EMF data for creation."""
    return {
        "emf_id": "EMF-001",
        "order_id": "ORD-001",
        "order_creation_date": "2024-01-15",
        "demand_id": "DEM-001",
        "demand_creation_date": "2024-01-10",
        "bikushit_id": "BIK-001",
        "bikushit_creation_date": "2024-01-20",
        "costs": [{"currency": "ILS", "amount": 1000.50}],
    }


@pytest.fixture
def sample_emf_data_no_costs() -> dict:
    """Sample EMF data for creation without costs."""
    return {
        "emf_id": "EMF-001",
        "order_id": "ORD-001",
        "order_creation_date": "2024-01-15",
        "demand_id": "DEM-001",
        "demand_creation_date": "2024-01-10",
        "bikushit_id": "BIK-001",
        "bikushit_creation_date": "2024-01-20",
    }


@pytest.fixture
def sample_emf(db_session, sample_purpose) -> EMF:
    """Create sample EMF."""
    emf = EMF(
        emf_id="EMF-001",
        purpose_id=sample_purpose.id,
        creation_date=date.today(),
        order_id="ORD-001",
        order_creation_date=date(2024, 1, 15),
        demand_id="DEM-001",
        demand_creation_date=date(2024, 1, 10),
        bikushit_id="BIK-001",
        bikushit_creation_date=date(2024, 1, 20),
    )
    db_session.add(emf)
    db_session.commit()
    db_session.refresh(emf)
    return emf
