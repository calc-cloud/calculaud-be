"""FastAPI router for stage endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.stages import service
from app.stages.exceptions import InvalidStageValue, StageNotFound
from app.stages.schemas import StageResponse, StageUpdate

router = APIRouter()


@router.patch("/{stage_id}", response_model=StageResponse)
def update_stage(
    stage_id: int,
    stage_update: StageUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a stage's value and/or completion date.

    - **stage_id**: The ID of the stage to update
    - **value**: New value for the stage (optional)
    - **completion_date**: Set completion date for the stage (optional)

    Supports partial updates - only provided fields will be updated.
    """
    try:
        updated_stage = service.update_stage(db, stage_id, stage_update)
        return updated_stage
    except StageNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)
    except InvalidStageValue as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/{stage_id}", response_model=StageResponse, operation_id="get_stage")
def get_stage(
    stage_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a stage by ID.

    - **stage_id**: The ID of the stage to retrieve
    """
    stage = service.get_stage(db, stage_id)
    if not stage:
        raise HTTPException(
            status_code=404, detail=f"Stage with ID {stage_id} not found"
        )
    return stage
