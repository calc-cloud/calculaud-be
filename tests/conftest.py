from datetime import date, datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import EMF, Cost, Hierarchy, Purpose

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db) -> TestClient:
    """Create test client with test database."""

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# Sample data fixtures
@pytest.fixture
def sample_hierarchy(db_session) -> Hierarchy:
    """Create sample hierarchy."""
    hierarchy = Hierarchy(type="unit", name="Test Unit")
    db_session.add(hierarchy)
    db_session.commit()
    db_session.refresh(hierarchy)
    return hierarchy


@pytest.fixture
def sample_purpose_data(sample_hierarchy) -> dict:
    """Sample purpose data for creation."""
    return {
        "hierarchy_id": sample_hierarchy.id,
        "excepted_delivery": "2024-12-31",
        "comments": "Test comments",
        "status": "Pending",
        "supplier": "Test Supplier",
        "content": "Test content",
        "description": "Test description",
        "service_type": "Consulting",
    }


@pytest.fixture
def sample_purpose(db_session, sample_hierarchy) -> Purpose:
    """Create sample purpose."""
    purpose = Purpose(
        hierarchy_id=sample_hierarchy.id,
        excepted_delivery=date(2024, 12, 31),
        comments="Test comments",
        status="Pending",
        supplier="Test Supplier",
        content="Test content",
        description="Test description",
        service_type="Consulting",
        creation_time=datetime.now(),
        last_modified=datetime.now(),
    )
    db_session.add(purpose)
    db_session.commit()
    db_session.refresh(purpose)
    return purpose


@pytest.fixture
def sample_emf_data() -> dict:
    """Sample EMF data for creation."""
    return {
        "emf_id": "EMF-001",
        "order_id": "ORD-001",
        "order_date": "2024-01-15",
        "demand_id": "DEM-001",
        "demand_date": "2024-01-10",
        "bikushit_id": "BIK-001",
        "bikushit_date": "2024-01-20",
    }


@pytest.fixture
def sample_emf(db_session, sample_purpose) -> EMF:
    """Create sample EMF."""
    emf = EMF(
        emf_id="EMF-001",
        purpose_id=sample_purpose.id,
        creation_time=datetime.now(),
        order_id="ORD-001",
        order_date=date(2024, 1, 15),
        demand_id="DEM-001",
        demand_date=date(2024, 1, 10),
        bikushit_id="BIK-001",
        bikushit_date=date(2024, 1, 20),
    )
    db_session.add(emf)
    db_session.commit()
    db_session.refresh(emf)
    return emf


@pytest.fixture
def sample_cost_data() -> dict:
    """Sample cost data for creation."""
    return {"currency": "ILS", "cost": 1000.50}


@pytest.fixture
def sample_cost(db_session, sample_emf) -> Cost:
    """Create sample cost."""
    cost = Cost(emf_id=sample_emf.id, currency="ILS", cost=1000.50)
    db_session.add(cost)
    db_session.commit()
    db_session.refresh(cost)
    return cost


@pytest.fixture
def sample_hierarchy_data() -> dict:
    """Sample hierarchy data for creation."""
    return {"type": "center", "name": "Test Center", "parent_id": None}
