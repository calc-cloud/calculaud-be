"""Predefined Flow-specific test fixtures."""

import pytest

from app import PredefinedFlow, StageType
from app.config import settings


# Stage Type fixtures for predefined flows
@pytest.fixture
def test_stage_types(db_session) -> list[StageType]:
    """Create test stage types for predefined flows."""
    stage_types = [
        StageType(
            name="approval",
            display_name="Approval Stage",
            description="Stage for approval processes",
            value_required=True,
        ),
        StageType(
            name="review",
            display_name="Review Stage",
            description="Stage for review processes",
            value_required=False,
        ),
        StageType(
            name="validation",
            display_name="Validation Stage",
            description="Stage for validation processes",
            value_required=True,
        ),
        StageType(
            name="completion",
            display_name="Completion Stage",
            description="Final completion stage",
            value_required=False,
        ),
        StageType(
            name="initialization",
            display_name="Initialization Stage",
            description="Initial stage setup",
            value_required=True,
        ),
    ]

    for stage_type in stage_types:
        db_session.add(stage_type)
    db_session.commit()

    for stage_type in stage_types:
        db_session.refresh(stage_type)

    return stage_types


# Predefined Flow fixtures
@pytest.fixture
def sample_predefined_flow_data(test_stage_types) -> dict:
    """Sample predefined flow data for creation."""
    stage_ids = [st.id for st in test_stage_types]
    return {
        "flow_name": "Standard Procurement Flow",
        "stages": [
            stage_ids[0],  # approval (priority 1)
            [stage_ids[1], stage_ids[2]],  # review and validation (priority 2)
            stage_ids[3],  # completion (priority 3)
        ],
    }


@pytest.fixture
def sample_predefined_flow(db_session, test_stage_types) -> PredefinedFlow:
    """Create sample predefined flow."""
    from app.predefined_flows.models import PredefinedFlowStage

    flow = PredefinedFlow(flow_name="Test Procurement Flow")
    db_session.add(flow)
    db_session.flush()

    # Add stages with priorities
    stage_1 = PredefinedFlowStage(
        predefined_flow_id=flow.id, stage_type_id=test_stage_types[0].id, priority=1
    )
    stage_2 = PredefinedFlowStage(
        predefined_flow_id=flow.id, stage_type_id=test_stage_types[1].id, priority=2
    )
    stage_3 = PredefinedFlowStage(
        predefined_flow_id=flow.id, stage_type_id=test_stage_types[2].id, priority=2
    )

    db_session.add_all([stage_1, stage_2, stage_3])
    db_session.commit()
    db_session.refresh(flow)
    return flow


@pytest.fixture
def multiple_predefined_flows(test_client, test_stage_types):
    """Create multiple predefined flows for pagination and search tests."""
    stage_ids = [st.id for st in test_stage_types]

    flows = [
        {
            "flow_name": "Standard Procurement Flow",
            "stages": [stage_ids[0], stage_ids[1], stage_ids[2]],
        },
        {
            "flow_name": "Express Procurement Flow",
            "stages": [stage_ids[0], stage_ids[3]],
        },
        {
            "flow_name": "Complex Approval Flow",
            "stages": [
                stage_ids[4],
                [stage_ids[0], stage_ids[1]],
                stage_ids[2],
                stage_ids[3],
            ],
        },
        {
            "flow_name": "Simple Review Flow",
            "stages": [stage_ids[1], stage_ids[3]],
        },
        {
            "flow_name": "Validation Only Flow",
            "stages": [stage_ids[2]],
        },
        {
            "flow_name": "Full Process Flow",
            "stages": [
                stage_ids[4],
                stage_ids[0],
                stage_ids[1],
                stage_ids[2],
                stage_ids[3],
            ],
        },
        {
            "flow_name": "Quick Approval Flow",
            "stages": [stage_ids[0], stage_ids[3]],
        },
        {
            "flow_name": "Multi-Stage Review Flow",
            "stages": [
                stage_ids[1],
                [stage_ids[0], stage_ids[2]],
                stage_ids[3],
            ],
        },
    ]

    created_flows = []
    for data in flows:
        response = test_client.post(
            f"{settings.api_v1_prefix}/predefined-flows", json=data
        )
        assert response.status_code == 201
        created_flows.append(response.json())

    return created_flows


@pytest.fixture
def search_predefined_flows(test_client, test_stage_types):
    """Create predefined flows specifically for search functionality tests."""
    stage_ids = [st.id for st in test_stage_types]

    flows = [
        {
            "flow_name": "Procurement Standard Flow",
            "stages": [stage_ids[0], stage_ids[1]],
        },
        {
            "flow_name": "Procurement Express Flow",
            "stages": [stage_ids[0], stage_ids[3]],
        },
        {
            "flow_name": "Procurement Complex Flow",
            "stages": [stage_ids[4], stage_ids[0], stage_ids[2]],
        },
        {
            "flow_name": "Approval Basic Flow",
            "stages": [stage_ids[0], stage_ids[3]],
        },
        {
            "flow_name": "Approval Advanced Flow",
            "stages": [stage_ids[4], stage_ids[0], stage_ids[1], stage_ids[3]],
        },
        {
            "flow_name": "Review Simple Flow",
            "stages": [stage_ids[1], stage_ids[3]],
        },
        {
            "flow_name": "Review Comprehensive Flow",
            "stages": [stage_ids[1], stage_ids[2], stage_ids[3]],
        },
        {
            "flow_name": "Validation Quick Flow",
            "stages": [stage_ids[2]],
        },
        {
            "flow_name": "Standard Process Flow",
            "stages": [stage_ids[0], stage_ids[1], stage_ids[2], stage_ids[3]],
        },
        {
            "flow_name": "Express Process Flow",
            "stages": [stage_ids[0], stage_ids[3]],
        },
    ]

    created_flows = []
    for data in flows:
        response = test_client.post(
            f"{settings.api_v1_prefix}/predefined-flows", json=data
        )
        assert response.status_code == 201
        created_flows.append(response.json())

    return created_flows