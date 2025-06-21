from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.service_types import service
from app.service_types.schemas import ServiceType, ServiceTypeCreate, ServiceTypeUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResult[ServiceType])
def get_service_types(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    """Get all service types with pagination."""
    service_types, total = service.get_service_types(db=db, pagination=pagination)
    return create_paginated_result(service_types, total, pagination)


@router.get("/{service_type_id}", response_model=ServiceType)
def get_service_type(service_type_id: int, db: Session = Depends(get_db)):
    """Get a specific service type by ID."""
    service_type = service.get_service_type(db, service_type_id)
    if not service_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found"
        )
    return service_type


@router.post("/", response_model=ServiceType, status_code=status.HTTP_201_CREATED)
def create_service_type(service_type: ServiceTypeCreate, db: Session = Depends(get_db)):
    """Create a new service type."""
    return service.create_service_type(db, service_type)


@router.patch("/{service_type_id}", response_model=ServiceType)
def patch_service_type(
    service_type_id: int,
    service_type_update: ServiceTypeUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing service type."""
    patched_service_type = service.patch_service_type(
        db, service_type_id, service_type_update
    )
    if not patched_service_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found"
        )
    return patched_service_type


@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_type(service_type_id: int, db: Session = Depends(get_db)):
    """Delete a service type."""
    if not service.delete_service_type(db, service_type_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service type not found"
        )