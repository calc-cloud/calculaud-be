"""Supplier-specific test fixtures."""

import pytest

from app.config import settings
from app.suppliers.models import Supplier


# Supplier fixtures
@pytest.fixture
def sample_supplier_data() -> dict:
    """Sample supplier data for creation."""
    return {"name": "Tech Solutions Inc"}


@pytest.fixture
def sample_supplier(db_session) -> Supplier:
    """Create sample supplier in database."""
    supplier = Supplier(name="Tech Solutions Inc")
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def sample_supplier_with_icon(db_session, sample_file_attachment) -> Supplier:
    """Create sample supplier with file icon in database."""
    supplier = Supplier(
        name="Tech Corp with Icon", file_icon_id=sample_file_attachment.id
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def multiple_suppliers(db_session) -> list[Supplier]:
    """Create multiple sample suppliers for pagination and search tests."""
    suppliers = [
        Supplier(name="Alpha Industries"),
        Supplier(name="Beta Solutions"),
        Supplier(name="Digital Solutions"),
        Supplier(name="Hardware Plus"),
        Supplier(name="IT Consulting"),
        Supplier(name="Software Services Ltd"),
        Supplier(name="Tech Solutions Inc"),
        Supplier(name="Zebra Corp"),
    ]
    db_session.add_all(suppliers)
    db_session.commit()
    for supplier in suppliers:
        db_session.refresh(supplier)
    return suppliers


@pytest.fixture
def search_suppliers(db_session) -> list[Supplier]:
    """Create suppliers specifically for search functionality tests."""
    suppliers = [
        Supplier(name="Tech Solutions Inc"),
        Supplier(name="Tech Hardware Plus"),
        Supplier(name="Software Tech Services"),
        Supplier(name="IT Tech Consulting"),
        Supplier(name="Digital Tech Solutions"),
        Supplier(name="Apple Computer"),
        Supplier(name="Microsoft Corporation"),
        Supplier(name="HARDWARE PLUS"),
        Supplier(name="software services ltd"),
        Supplier(name="It Consulting"),
    ]
    db_session.add_all(suppliers)
    db_session.commit()
    for supplier in suppliers:
        db_session.refresh(supplier)
    return suppliers


@pytest.fixture
def multiple_suppliers_for_filtering(test_client):
    """Create multiple suppliers for purpose filtering tests."""
    supplier_a = test_client.post(
        f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier A"}
    ).json()

    supplier_b = test_client.post(
        f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier B"}
    ).json()

    return {"supplier_a": supplier_a, "supplier_b": supplier_b}
