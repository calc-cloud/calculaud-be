from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as statuses
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, create_paginated_result
from app.purposes import service
from app.purposes.exceptions import DuplicateServiceInPurpose, ServiceNotFound
from app.purposes.schemas import (
    GetPurposesRequest,
    Purpose,
    PurposeCreate,
    PurposeUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Purpose])
def get_purposes(
    params: Annotated[GetPurposesRequest, Query()],
    db: Session = Depends(get_db),
):
    """Get all purposes with filtering, searching, sorting, and pagination."""
    purposes, total = service.get_purposes(
        db=db,
        params=params,
    )

    return create_paginated_result(purposes, total, params)


@router.get("/{purpose_id}", response_model=Purpose)
def get_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """Get a specific purpose by ID."""
    purpose = service.get_purpose(db, purpose_id)
    if not purpose:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
    return purpose


@router.post("/", response_model=Purpose, status_code=statuses.HTTP_201_CREATED)
def create_purpose(purpose: PurposeCreate, db: Session = Depends(get_db)):
    """Create a new purpose."""
    try:
        return service.create_purpose(db, purpose)
    except (ServiceNotFound, DuplicateServiceInPurpose) as e:
        raise HTTPException(status_code=statuses.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{purpose_id}", response_model=Purpose)
def patch_purpose(
    purpose_id: int, purpose_update: PurposeUpdate, db: Session = Depends(get_db)
):
    """Patch an existing purpose."""
    try:
        patched_purpose = service.patch_purpose(db, purpose_id, purpose_update)
        if not patched_purpose:
            raise HTTPException(
                status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
            )
        return patched_purpose
    except (ServiceNotFound, DuplicateServiceInPurpose) as e:
        raise HTTPException(status_code=statuses.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{purpose_id}", status_code=statuses.HTTP_204_NO_CONTENT)
def delete_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """Delete a purpose."""
    if not service.delete_purpose(db, purpose_id):
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
