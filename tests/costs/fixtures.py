"""Cost-specific test fixtures."""

import pytest

from app import Cost


# Cost fixtures
@pytest.fixture
def sample_cost_data() -> dict:
    """Sample cost data for creation."""
    return {"currency": "ILS", "amount": 1000.50}


@pytest.fixture
def sample_cost(db_session, sample_purchase) -> Cost:
    """Create sample cost."""
    cost = Cost(purchase_id=sample_purchase.id, currency="ILS", amount=1000.50)
    db_session.add(cost)
    db_session.commit()
    db_session.refresh(cost)
    return cost
