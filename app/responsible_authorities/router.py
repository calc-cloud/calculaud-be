from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.responsible_authorities import service
from app.responsible_authorities.exceptions import (
    ResponsibleAuthorityAlreadyExists,
    ResponsibleAuthorityNotFound,
)
from app.responsible_authorities.schemas import (
    ResponsibleAuthorityCreate,
    ResponsibleAuthorityResponse,
    ResponsibleAuthorityUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResult[ResponsibleAuthorityResponse],
    operation_id="get_responsible_authorities",
)
def get_responsible_authorities(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search authorities by name (case-insensitive)"
    ),
    db: Session = Depends(get_db),
):
    """Get responsible authorities with pagination and search support."""
    authorities, total = service.get_responsible_authorities(
        db=db, pagination=pagination, search=search
    )
    return create_paginated_result(authorities, total, pagination)


@router.get(
    "/{authority_id}",
    response_model=ResponsibleAuthorityResponse,
    operation_id="get_responsible_authority",
)
def get_responsible_authority(authority_id: int, db: Session = Depends(get_db)):
    """Get specific responsible authority by ID."""
    authority = service.get_responsible_authority(db, authority_id)
    if not authority:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsible authority not found",
        )
    return authority


@router.post(
    "/",
    response_model=ResponsibleAuthorityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_responsible_authority(
    authority: ResponsibleAuthorityCreate, db: Session = Depends(get_db)
):
    """Create a new responsible authority."""
    try:
        return service.create_responsible_authority(db, authority)
    except ResponsibleAuthorityAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.patch("/{authority_id}", response_model=ResponsibleAuthorityResponse)
def patch_responsible_authority(
    authority_id: int,
    authority_update: ResponsibleAuthorityUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing responsible authority."""
    try:
        return service.patch_responsible_authority(db, authority_id, authority_update)
    except ResponsibleAuthorityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ResponsibleAuthorityAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.delete("/{authority_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_responsible_authority(authority_id: int, db: Session = Depends(get_db)):
    """Delete a responsible authority."""
    try:
        service.delete_responsible_authority(db, authority_id)
    except ResponsibleAuthorityNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
