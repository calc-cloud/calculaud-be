"""Test fixtures for stage tests."""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.stage_types.models import StageType
from app.stages.models import Stage


@pytest.fixture
def sample_stage_data():
    """Sample stage creation data."""
    return {"value": "TEST-STAGE-001", "completion_date": None}


@pytest.fixture
def sample_stage_update_data():
    """Sample stage update data."""
    return {"value": "UPDATED-STAGE-001", "completion_date": datetime.now()}


@pytest.fixture
def sample_stage(
    db_session: Session, sample_purpose, sample_purchase, required_value_stage_type
):
    """Create a sample stage in the database with a stage type that allows values."""
    stage = Stage(
        stage_type_id=required_value_stage_type.id,
        purchase_id=sample_purchase.id,
        priority=1,
        value="TEST-STAGE-001",
        completion_date=None,
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage


@pytest.fixture
def completed_stage(
    db_session: Session, sample_purpose, sample_purchase, required_value_stage_type
):
    """Create a completed stage in the database."""
    stage = Stage(
        stage_type_id=required_value_stage_type.id,
        purchase_id=sample_purchase.id,
        priority=1,
        value="COMPLETED-STAGE-001",
        completion_date=datetime.now(),
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage


@pytest.fixture
def required_value_stage_type(db_session: Session):
    """Create a stage type that requires a value."""
    stage_type = StageType(
        name="required_value_stage",
        display_name="Required Value Stage",
        value_required=True,
    )
    db_session.add(stage_type)
    db_session.commit()
    db_session.refresh(stage_type)
    return stage_type


@pytest.fixture
def no_value_stage_type(db_session: Session):
    """Create a stage type that does not allow values."""
    stage_type = StageType(
        name="no_value_stage",
        display_name="No Value Stage",
        value_required=False,
    )
    db_session.add(stage_type)
    db_session.commit()
    db_session.refresh(stage_type)
    return stage_type


# Keep old name for backward compatibility
optional_value_stage_type = no_value_stage_type
