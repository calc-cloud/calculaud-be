"""Stage Type-specific test fixtures."""

import pytest

from app import StageType
from app.config import settings


# Stage Type fixtures
@pytest.fixture
def sample_stage_type_data() -> dict:
    """Sample stage type data for creation."""
    return {
        "name": "approval",
        "display_name": "Approval Stage",
        "description": "Stage for approval processes",
        "value_required": True,
    }


@pytest.fixture
def sample_stage_type(db_session) -> StageType:
    """Create sample stage type."""
    stage_type = StageType(
        name="test_stage",
        display_name="Test Stage",
        description="Test stage description",
        value_required=False,
    )
    db_session.add(stage_type)
    db_session.commit()
    db_session.refresh(stage_type)
    return stage_type


@pytest.fixture
def multiple_stage_types(test_client):
    """Create multiple stage types for pagination and search tests."""
    stage_types = [
        {
            "name": "approval",
            "display_name": "Approval Stage",
            "description": "Stage for approval processes",
            "value_required": True,
        },
        {
            "name": "review",
            "display_name": "Review Stage",
            "description": "Stage for review processes",
            "value_required": False,
        },
        {
            "name": "validation",
            "display_name": "Validation Stage",
            "description": "Stage for validation processes",
            "value_required": True,
        },
        {
            "name": "completion",
            "display_name": "Completion Stage",
            "description": "Final completion stage",
            "value_required": False,
        },
        {
            "name": "initialization",
            "display_name": "Initialization Stage",
            "description": "Initial stage setup",
            "value_required": True,
        },
        {
            "name": "processing",
            "display_name": "Processing Stage",
            "description": "Main processing stage",
            "value_required": False,
        },
        {
            "name": "finalization",
            "display_name": "Finalization Stage",
            "description": "Final stage processes",
            "value_required": True,
        },
        {
            "name": "archival",
            "display_name": "Archival Stage",
            "description": "Archive completed items",
            "value_required": False,
        },
    ]

    created_stage_types = []
    for data in stage_types:
        response = test_client.post(f"{settings.api_v1_prefix}/stage-types", json=data)
        assert response.status_code == 201
        created_stage_types.append(response.json())

    return created_stage_types


@pytest.fixture
def search_stage_types(test_client):
    """Create stage types specifically for search functionality tests."""
    stage_types = [
        {
            "name": "approval_basic",
            "display_name": "Basic Approval",
            "description": "Basic approval process",
            "value_required": True,
        },
        {
            "name": "approval_advanced",
            "display_name": "Advanced Approval",
            "description": "Advanced approval process",
            "value_required": True,
        },
        {
            "name": "approval_simple",
            "display_name": "Simple Approval",
            "description": "Simple approval process",
            "value_required": False,
        },
        {
            "name": "review_basic",
            "display_name": "Basic Review",
            "description": "Basic review process",
            "value_required": False,
        },
        {
            "name": "validation_input",
            "display_name": "Input Validation",
            "description": "Validate input data",
            "value_required": True,
        },
        {
            "name": "validation_output",
            "display_name": "Output Validation",
            "description": "Validate output data",
            "value_required": True,
        },
        {
            "name": "processing_main",
            "display_name": "Main Processing",
            "description": "Main data processing",
            "value_required": False,
        },
        {
            "name": "processing_batch",
            "display_name": "Batch Processing",
            "description": "Batch data processing",
            "value_required": False,
        },
        {
            "name": "completion_final",
            "display_name": "Final Completion",
            "description": "Final completion check",
            "value_required": True,
        },
        {
            "name": "archival_long_term",
            "display_name": "Long Term Archive",
            "description": "Long term archival process",
            "value_required": False,
        },
    ]

    created_stage_types = []
    for data in stage_types:
        response = test_client.post(f"{settings.api_v1_prefix}/stage-types", json=data)
        assert response.status_code == 201
        created_stage_types.append(response.json())

    return created_stage_types
