"""Cost-specific test fixtures."""

import pytest

from app import Cost


# Cost fixtures
@pytest.fixture
def sample_cost_data() -> dict:
    """Sample cost data for creation."""
    return {"currency": "ILS", "amount": 1000.50}


@pytest.fixture
def sample_cost(db_session, sample_emf) -> Cost:
    """Create sample cost."""
    cost = Cost(emf_id=sample_emf.id, currency="ILS", cost=1000.50)
    db_session.add(cost)
    db_session.commit()
    db_session.refresh(cost)
    return cost
