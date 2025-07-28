"""Global test fixtures for database setup and common utilities."""

import os

# Set testing environment variable
os.environ["TESTING"] = "1"

from typing import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.auth.dependencies import require_auth  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from tests.auth_mock import (  # noqa: E402
    mock_auth_dependency,
    mock_auth_dependency_no_admin,
)

pytest_plugins = [
    "tests.hierarchies.fixtures",
    "tests.files.fixtures",
    "tests.predefined_flows.fixtures",
    "tests.purchases.fixtures",
    "tests.purposes.fixtures",
    "tests.services.fixtures",
    "tests.service_types.fixtures",
    "tests.stage_types.fixtures",
    "tests.stages.fixtures",
    "tests.costs.fixtures",
    "tests.suppliers.fixtures",
]

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def test_db() -> Generator:
    """Create test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    """Shared database override function for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create test client with test database and mock authentication."""
    # Override dependencies for testing
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = mock_auth_dependency

    client = TestClient(app)

    # Clean up overrides after test
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client_no_admin(test_db):
    """Create test client with test database and mock regular user authentication."""
    # Override dependencies for testing with regular user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = mock_auth_dependency_no_admin

    client = TestClient(app)

    # Clean up overrides after test
    yield client
    app.dependency_overrides.clear()
