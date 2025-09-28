"""Test fixtures for purchase tests."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import Stage
from app.costs.models import CurrencyEnum
from app.predefined_flows.models import PredefinedFlow, PredefinedFlowStage
from app.purchases import service as purchase_service
from app.purchases.consts import PredefinedFlowName
from app.purchases.schemas import PurchaseCreate
from app.stage_types.models import StageType


@pytest.fixture
def sample_purchase_data():
    """Sample purchase creation data."""
    return {"purpose_id": 1}


@pytest.fixture
def sample_purchase_data_with_budget_source(sample_budget_source):
    """Sample purchase creation data with budget source."""
    return {"purpose_id": 1, "budget_source_id": sample_budget_source.id}


@pytest.fixture
def sample_purchase_data_with_costs():
    """Sample purchase creation data with costs."""
    return {
        "purpose_id": 1,
        "costs": [
            {"currency": CurrencyEnum.SUPPORT_USD.value, "amount": 50000.0},
            {"currency": CurrencyEnum.ILS.value, "amount": 10000.0},
        ],
    }


@pytest.fixture
def sample_purchase_data_with_costs_and_budget_source(sample_budget_source):
    """Sample purchase creation data with costs and budget source."""
    return {
        "purpose_id": 1,
        "budget_source_id": sample_budget_source.id,
        "costs": [
            {"currency": CurrencyEnum.SUPPORT_USD.value, "amount": 50000.0},
            {"currency": CurrencyEnum.ILS.value, "amount": 10000.0},
        ],
    }


@pytest.fixture
def sample_purchase_data_support_usd_above_400k():
    """Sample purchase creation data with SUPPORT_USD above 400k."""
    return {
        "purpose_id": 1,
        "costs": [{"currency": CurrencyEnum.SUPPORT_USD.value, "amount": 150000.0}],
    }


@pytest.fixture
def sample_purchase_data_available_usd():
    """Sample purchase creation data with AVAILABLE_USD."""
    return {
        "purpose_id": 1,
        "costs": [{"currency": CurrencyEnum.AVAILABLE_USD.value, "amount": 75000.0}],
    }


@pytest.fixture
def sample_purchase_data_ils():
    """Sample purchase creation data with ILS."""
    return {
        "purpose_id": 1,
        "costs": [{"currency": CurrencyEnum.ILS.value, "amount": 25000.0}],
    }


@pytest.fixture
def sample_purchase_create_data(sample_purchase_data):
    """Sample purchase creation data as PurchaseCreate schema."""
    return PurchaseCreate(**sample_purchase_data)


@pytest.fixture
def sample_purchase_create_data_with_budget_source(
    sample_purchase_data_with_budget_source,
):
    """Sample purchase creation data with budget source as PurchaseCreate schema."""
    return PurchaseCreate(**sample_purchase_data_with_budget_source)


@pytest.fixture
def sample_purchase_create_data_with_costs(sample_purchase_data_with_costs):
    """Sample purchase creation data with costs as PurchaseCreate schema."""
    return PurchaseCreate(**sample_purchase_data_with_costs)


@pytest.fixture
def sample_purchase_create_data_with_costs_and_budget_source(
    sample_purchase_data_with_costs_and_budget_source,
):
    """Sample purchase creation data with costs and budget source as PurchaseCreate schema."""
    return PurchaseCreate(**sample_purchase_data_with_costs_and_budget_source)


@pytest.fixture
def sample_purchase_update_data(sample_budget_source):
    """Sample purchase update data for PATCH operations."""
    return {"budget_source_id": sample_budget_source.id}


@pytest.fixture
def sample_purchase_update_data_null():
    """Sample purchase update data to remove budget source."""
    return {"budget_source_id": None}


@pytest.fixture
def sample_purchase_with_budget_source(
    db_session: Session, sample_purchase_create_data_with_budget_source: PurchaseCreate
):
    """Create sample purchase with budget source for update tests."""
    return purchase_service.create_purchase(
        db_session, sample_purchase_create_data_with_budget_source
    )


@pytest.fixture
def sample_purchase(db_session: Session, sample_purchase_create_data: PurchaseCreate):
    """Create a sample purchase in the database."""
    return purchase_service.create_purchase(db_session, sample_purchase_create_data)


@pytest.fixture
def sample_purchase_with_costs(
    db_session: Session,
    sample_purchase_create_data_with_costs: PurchaseCreate,
    predefined_flows_for_purchases,
):
    """Create a sample purchase with costs in the database."""
    return purchase_service.create_purchase(
        db_session, sample_purchase_create_data_with_costs
    )


@pytest.fixture
def predefined_flows_for_purchases(db_session: Session):
    """Create predefined flows needed for purchase flow selection."""
    # Create basic stage types
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
    ]

    for stage_type in stage_types:
        db_session.add(stage_type)
    db_session.flush()

    # Create predefined flows that match the purchase logic
    flows_config = [
        (PredefinedFlowName.ILS_FLOW.value, [0, 3]),  # approval -> completion
        (
            PredefinedFlowName.SUPPORT_USD_FLOW.value,
            [0, 1, 3],
        ),  # approval -> review -> completion
        (
            PredefinedFlowName.AVAILABLE_USD_FLOW.value,
            [0, 2, 3],
        ),  # approval -> validation -> completion
        (
            PredefinedFlowName.MIXED_USD_FLOW.value,
            [0, 1, 2, 3],
        ),  # approval -> review -> validation -> completion
        (
            PredefinedFlowName.SUPPORT_USD_ABOVE_400K_FLOW.value,
            [0, 1, 2, 3],
        ),  # approval -> review -> validation -> completion
        (
            PredefinedFlowName.MIXED_USD_ABOVE_400K_FLOW.value,
            [0, 1, 2, 3],
        ),  # approval -> review -> validation -> completion
    ]

    flows = []
    for flow_name, stage_indices in flows_config:
        flow = PredefinedFlow(flow_name=flow_name)
        db_session.add(flow)
        db_session.flush()

        # Add stages with priority
        for priority, stage_index in enumerate(stage_indices, 1):
            flow_stage = PredefinedFlowStage(
                predefined_flow_id=flow.id,
                stage_type_id=stage_types[stage_index].id,
                priority=priority,
            )
            db_session.add(flow_stage)

        flows.append(flow)

    db_session.commit()
    return flows


@pytest.fixture
def stage_types_for_purchases(db_session: Session):
    """Create stage types for purchase stage management tests."""
    stage_types = [
        StageType(
            name="initial_review",
            display_name="Initial Review",
            description="Initial review stage",
            value_required=False,
        ),
        StageType(
            name="final_approval",
            display_name="Final Approval",
            description="Final approval stage",
            value_required=True,
        ),
        StageType(
            name="procurement",
            display_name="Procurement",
            description="Procurement stage",
            value_required=False,
        ),
    ]

    for stage_type in stage_types:
        db_session.add(stage_type)
    db_session.commit()
    return stage_types


@pytest.fixture
def sample_purchase_with_stages(
    db_session: Session,
    sample_purchase_create_data_with_costs: PurchaseCreate,
    predefined_flows_for_purchases,
):
    """Create a sample purchase with stages for stage management tests."""
    return purchase_service.create_purchase(
        db_session, sample_purchase_create_data_with_costs
    )


@pytest.fixture
def sample_purchase_with_completed_stage(
    db_session: Session,
    sample_purchase_with_stages,
):
    """Create a purchase with one completed stage for preservation tests."""

    # Get the first stage and mark it as completed

    stmt = select(Stage).where(
        Stage.purchase_id == sample_purchase_with_stages.id, Stage.priority == 1
    )
    first_stage = db_session.execute(stmt).scalar_one_or_none()

    if first_stage:
        first_stage.value = "Completed with approval"
        first_stage.completion_date = date.today()
        db_session.commit()

    return sample_purchase_with_stages
