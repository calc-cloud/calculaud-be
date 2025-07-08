"""Service layer for stage operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.stages.exceptions import InvalidStageValue, StageNotFound
from app.stages.models import Stage
from app.stages.schemas import StageUpdate


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
