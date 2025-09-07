"""Budget source-specific test fixtures."""

import pytest

from app.budget_sources.models import BudgetSource
from app.config import settings


# Budget source fixtures
@pytest.fixture
def sample_budget_source_data() -> dict:
    """Sample budget source data for creation."""
    return {"name": "Federal Budget 2024"}


@pytest.fixture
def sample_budget_source(db_session) -> BudgetSource:
    """Create sample budget source in database."""
    budget_source = BudgetSource(name="Federal Budget 2024")
    db_session.add(budget_source)
    db_session.commit()
    db_session.refresh(budget_source)
    return budget_source


@pytest.fixture
def multiple_budget_sources(db_session) -> list[BudgetSource]:
    """Create multiple sample budget sources for pagination and search tests."""
    budget_sources = [
        BudgetSource(name="Capital Expenditure Fund"),
        BudgetSource(name="Discretionary Budget"),
        BudgetSource(name="Emergency Fund"),
        BudgetSource(name="Federal Budget 2024"),
        BudgetSource(name="Infrastructure Fund"),
        BudgetSource(name="Operating Budget"),
        BudgetSource(name="Research Grant"),
        BudgetSource(name="Special Projects Fund"),
    ]
    db_session.add_all(budget_sources)
    db_session.commit()
    for budget_source in budget_sources:
        db_session.refresh(budget_source)
    return budget_sources


@pytest.fixture
def search_budget_sources(db_session) -> list[BudgetSource]:
    """Create budget sources specifically for search functionality tests."""
    budget_sources = [
        BudgetSource(name="Federal Budget 2024"),
        BudgetSource(name="Federal Reserve Fund"),
        BudgetSource(name="State Budget 2024"),
        BudgetSource(name="Municipal Budget"),
        BudgetSource(name="FEDERAL GRANT"),
        BudgetSource(name="emergency fund"),
        BudgetSource(name="Capital Budget"),
        BudgetSource(name="Research Budget 2024"),
        BudgetSource(name="Infrastructure Budget"),
        BudgetSource(name="Special Federal Fund"),
    ]
    db_session.add_all(budget_sources)
    db_session.commit()
    for budget_source in budget_sources:
        db_session.refresh(budget_source)
    return budget_sources


@pytest.fixture
def multiple_budget_sources_for_filtering(test_client):
    """Create multiple budget sources for filtering tests."""
    budget_source_a = test_client.post(
        f"{settings.api_v1_prefix}/budget-sources", json={"name": "Budget Source A"}
    ).json()

    budget_source_b = test_client.post(
        f"{settings.api_v1_prefix}/budget-sources", json={"name": "Budget Source B"}
    ).json()

    return {"budget_source_a": budget_source_a, "budget_source_b": budget_source_b}
