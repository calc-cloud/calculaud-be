"""Test fixtures for purchase tests."""

import pytest
from sqlalchemy.orm import Session

from app.purchases.models import Purchase
from app.purchases.schemas import PurchaseCreate


@pytest.fixture
def sample_purchase_data():
    """Sample purchase creation data."""
    return {"purpose_id": 1}


@pytest.fixture
def sample_purchase_create_data(sample_purchase_data):
    """Sample purchase creation data as PurchaseCreate schema."""
    return PurchaseCreate(**sample_purchase_data)


@pytest.fixture
def sample_purchase(db_session: Session, sample_purchase_create_data: PurchaseCreate):
    """Create a sample purchase in the database."""
    purchase = Purchase(**sample_purchase_create_data.model_dump())
    db_session.add(purchase)
    db_session.commit()
    db_session.refresh(purchase)
    return purchase
