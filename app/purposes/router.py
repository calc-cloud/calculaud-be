from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as statuses
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.purposes import service
from app.purposes.models import StatusEnum
from app.purposes.schemas import Purpose, PurposeCreate, PurposeUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Purpose])
def get_purposes(
    pagination: PaginationParams = Depends(),
    hierarchy_id: int | None = Query(None, description="Filter by hierarchy ID"),
    supplier_id: int | None = Query(None, description="Filter by supplier ID"),
    service_type_id: int | None = Query(None, description="Filter by service type ID"),
    status: StatusEnum | None = Query(None, description="Filter by status"),
    search: str
    | None = Query(None, description="Search in description, content, and supplier"),
    sort_by: str = Query("creation_time", description="Sort by field"),
    sort_order: Literal["asc", "desc"] = Query(
        "desc", description="Sort order: asc or desc"
    ),
    db: Session = Depends(get_db),
):
    """Get all purposes with filtering, searching, sorting, and pagination."""
    purposes, total = service.get_purposes(
        db=db,
        pagination=pagination,
        hierarchy_id=hierarchy_id,
        supplier_id=supplier_id,
        service_type_id=service_type_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return create_paginated_result(purposes, total, pagination)


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
    return service.create_purpose(db, purpose)


@router.patch("/{purpose_id}", response_model=Purpose)
def patch_purpose(
    purpose_id: int, purpose_update: PurposeUpdate, db: Session = Depends(get_db)
):
    """Patch an existing purpose."""
    patched_purpose = service.patch_purpose(db, purpose_id, purpose_update)
    if not patched_purpose:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
    return patched_purpose


@router.delete("/{purpose_id}", status_code=statuses.HTTP_204_NO_CONTENT)
def delete_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """Delete a purpose."""
    if not service.delete_purpose(db, purpose_id):
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
