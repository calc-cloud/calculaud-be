"""Service layer for stage operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.predefined_flows.models import PredefinedFlow
from app.purchases.schemas import StageEditItem
from app.stages.exceptions import InvalidStageValue, StageNotFound
from app.stages.models import Stage
from app.stages.schemas import StageUpdate
from app.stages.utils import validate_stage_edits


def get_stage(db: Session, stage_id: int) -> Stage | None:
    """Get a single stage by ID with stage_type relationship loaded."""
    stmt = (
        select(Stage).options(joinedload(Stage.stage_type)).where(Stage.id == stage_id)
    )
    return db.execute(stmt).unique().scalars().first()


def update_stage(db: Session, stage_id: int, stage_update: StageUpdate) -> Stage | None:
    """Update a stage with new value and/or completion date."""
    # Get the stage with stage_type loaded for validation
    stage = get_stage(db, stage_id)
    if not stage:
        raise StageNotFound(stage_id)

    # Validate value if provided
    if stage_update.value is not None and not stage.stage_type.value_required:
        raise InvalidStageValue(
            stage.stage_type.name, "values are not allowed for this stage type"
        )

    # Update only the fields that were provided (partial update)
    update_data = stage_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(stage, field, value)

    db.commit()
    db.refresh(stage)
    return stage


def create_stages_from_flow(
    db: Session, purchase_id: int, predefined_flow: PredefinedFlow
) -> list[Stage]:
    """
    Create stages for a purchase based on a predefined flow.

    Args:
        db: Database session
        purchase_id: ID of the purchase to create stages for
        predefined_flow: Predefined flow with stage definitions

    Returns:
        List of created Stage objects
    """
    stages = [
        Stage(
            stage_type_id=predefined_stage.stage_type_id,
            priority=predefined_stage.priority,
            purchase_id=purchase_id,
        )
        for predefined_stage in predefined_flow.predefined_flow_stages
    ]

    db.add_all(stages)
    return stages


def create_stages_from_edits(
    db: Session, purchase_id: int, stage_edits: list[StageEditItem]
) -> list[Stage]:
    """
    Create/update stages for a purchase based on stage edits.

    This function handles the complete replacement of purchase stages:
    1. Validates all stage edits
    2. Preserves data from existing stages (value, completion_date)
    3. Creates new stages as specified
    4. Assigns priorities based on array position

    Args:
        db: Database session
        purchase_id: ID of the purchase to update stages for
        stage_edits: List of stage edits (nested structure supported)

    Returns:
        List of Stage objects (new and updated)

    Raises:
        StageNotFound: If referenced stage doesn't exist or doesn't belong to purchase
        StageTypeNotFound: If stage_type_id doesn't exist
    """
    # Validate all stage edits and get flattened structure
    flattened_edits = validate_stage_edits(db, stage_edits, purchase_id)

    # Get existing stages for this purchase
    stmt = select(Stage).where(Stage.purchase_id == purchase_id)
    existing_stages = {stage.id: stage for stage in db.execute(stmt).scalars().all()}

    # Create new stage list
    new_stages = []

    for stage_edit, priority in flattened_edits:
        if stage_edit.id is not None:
            # Update existing stage with new priority, preserve data
            existing_stage = existing_stages[stage_edit.id]
            existing_stage.priority = priority
            new_stages.append(existing_stage)
        else:
            # Create new stage
            new_stage = Stage(
                stage_type_id=stage_edit.stage_type_id,
                priority=priority,
                purchase_id=purchase_id,
            )
            db.add(new_stage)
            new_stages.append(new_stage)

    # Remove stages that are no longer referenced
    referenced_stage_ids = {
        edit.id for edit, _ in flattened_edits if edit.id is not None
    }
    for stage_id, stage in existing_stages.items():
        if stage_id not in referenced_stage_ids:
            db.delete(stage)

    return new_stages
