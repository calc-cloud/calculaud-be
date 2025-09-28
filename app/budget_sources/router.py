from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.budget_sources import service
from app.budget_sources.exceptions import (
    BudgetSourceAlreadyExists,
    BudgetSourceNotFound,
)
from app.budget_sources.schemas import (
    BudgetSource,
    BudgetSourceCreate,
    BudgetSourceUpdate,
)
from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result

router = APIRouter()


@router.get("/", response_model=PaginatedResult[BudgetSource])
def get_budget_sources(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search budget sources by name (case-insensitive)"
    ),
    db: Session = Depends(get_db),
):
    """Get all budget sources with pagination and optional search."""
    budget_sources, total = service.get_budget_sources(
        db=db, pagination=pagination, search=search
    )
    return create_paginated_result(budget_sources, total, pagination)


@router.get("/{budget_source_id}", response_model=BudgetSource)
def get_budget_source(budget_source_id: int, db: Session = Depends(get_db)):
    """Get a specific budget source by ID."""
    budget_source = service.get_budget_source(db, budget_source_id)
    if not budget_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget source not found"
        )
    return budget_source


@router.post(
    "/",
    response_model=BudgetSource,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_budget_source(
    budget_source: BudgetSourceCreate,
    db: Session = Depends(get_db),
):
    """Create a new budget source."""
    try:
        return service.create_budget_source(db, budget_source)
    except BudgetSourceAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.patch(
    "/{budget_source_id}",
    response_model=BudgetSource,
    dependencies=[Depends(require_admin)],
)
def patch_budget_source(
    budget_source_id: int,
    budget_source_update: BudgetSourceUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing budget source."""
    try:
        return service.patch_budget_source(db, budget_source_id, budget_source_update)
    except BudgetSourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except BudgetSourceAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.delete(
    "/{budget_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_budget_source(
    budget_source_id: int,
    db: Session = Depends(get_db),
):
    """Delete a budget source."""
    try:
        service.delete_budget_source(db, budget_source_id)
    except BudgetSourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
