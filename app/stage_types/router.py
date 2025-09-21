from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.stage_types import service
from app.stage_types.exceptions import StageTypeAlreadyExists, StageTypeNotFound
from app.stage_types.schemas import StageTypeCreate, StageTypeResponse, StageTypeUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResult[StageTypeResponse])
def get_stage_types(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search stage types by name (case-insensitive)"
    ),
    db: Session = Depends(get_db),
):
    """Get all stage types with pagination and optional search."""
    stage_types, total = service.get_stage_types(
        db=db, pagination=pagination, search=search
    )
    return create_paginated_result(stage_types, total, pagination)


@router.get("/{stage_type_id}", response_model=StageTypeResponse)
def get_stage_type(stage_type_id: int, db: Session = Depends(get_db)):
    """Get a specific stage type by ID."""
    stage_type = service.get_stage_type(db, stage_type_id)
    if not stage_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stage type not found"
        )
    return stage_type


@router.post(
    "/",
    response_model=StageTypeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_stage_type(
    stage_type: StageTypeCreate,
    db: Session = Depends(get_db),
):
    """Create a new stage type."""
    try:
        return service.create_stage_type(db, stage_type)
    except StageTypeAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.patch(
    "/{stage_type_id}",
    response_model=StageTypeResponse,
    dependencies=[Depends(require_admin)],
)
def patch_stage_type(
    stage_type_id: int,
    stage_type_update: StageTypeUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing stage type."""
    try:
        return service.patch_stage_type(db, stage_type_id, stage_type_update)
    except StageTypeNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except StageTypeAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.delete(
    "/{stage_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_stage_type(
    stage_type_id: int,
    db: Session = Depends(get_db),
):
    """Delete a stage type."""
    try:
        service.delete_stage_type(db, stage_type_id)
    except StageTypeNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
