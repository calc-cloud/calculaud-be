"""Utility functions for stage management."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.purchases.schemas import StageEdit, StageEditItem
from app.stage_types.exceptions import StageTypeNotFound
from app.stage_types.models import StageType
from app.stages.exceptions import StageNotFound
from app.stages.models import Stage


def flatten_stage_edits_with_priorities(
    stage_edits: list[StageEditItem],
) -> list[tuple[StageEdit, int]]:
    """
    Flatten nested stage structure and assign priorities based on position.

    Args:
        stage_edits: List of StageEdit or list[StageEdit] items

    Returns:
        List of tuples (StageEdit, priority) with priorities starting from 1

    Example:
        Input: [stage1, [stage2, stage3], stage4]
        Output: [(stage1, 1), (stage2, 2), (stage3, 2), (stage4, 3)]
    """
    flattened = []
    priority = 1

    for item in stage_edits:
        if isinstance(item, list):
            # Multiple stages at same priority
            for stage_edit in item:
                flattened.append((stage_edit, priority))
        else:
            # Single stage
            flattened.append((item, priority))
        priority += 1

    return flattened


def _validate_stage_edit(db: Session, stage_edit: StageEdit, purchase_id: int) -> None:
    """
    Validate a stage edit for consistency and existence.

    Args:
        db: Database session
        stage_edit: StageEdit to validate
        purchase_id: ID of the purchase to validate against

    Raises:
        StageNotFound: If stage ID doesn't exist or doesn't belong to purchase
        StageTypeNotFound: If stage_type_id doesn't exist
    """
    if stage_edit.id is not None:
        # Validate existing stage
        stmt = select(Stage).where(
            Stage.id == stage_edit.id, Stage.purchase_id == purchase_id
        )
        existing_stage = db.execute(stmt).scalar_one_or_none()
        if not existing_stage:
            raise StageNotFound(stage_edit.id)

    if stage_edit.stage_type_id is not None:
        # Validate stage type exists
        stmt = select(StageType).where(StageType.id == stage_edit.stage_type_id)
        stage_type = db.execute(stmt).scalar_one_or_none()
        if not stage_type:
            raise StageTypeNotFound(stage_edit.stage_type_id)


def validate_stage_edits(
    db: Session, stage_edits: list[StageEditItem], purchase_id: int
) -> list[tuple[StageEdit, int]]:
    """
    Validate all stage edits in a nested structure and return flattened result.

    Args:
        db: Database session
        stage_edits: List of stage edits to validate
        purchase_id: ID of the purchase to validate against

    Returns:
        List of tuples (StageEdit, priority) with priorities starting from 1

    Raises:
        StageNotFound: If any stage ID doesn't exist or doesn't belong to purchase
        StageTypeNotFound: If any stage_type_id doesn't exist
    """
    flattened_edits = flatten_stage_edits_with_priorities(stage_edits)

    for stage_edit, _ in flattened_edits:
        _validate_stage_edit(db, stage_edit, purchase_id)

    return flattened_edits
