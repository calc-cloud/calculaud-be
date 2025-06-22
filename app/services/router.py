from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.services import service
from app.services.exceptions import InvalidServiceTypeId, ServiceAlreadyExists
from app.services.schemas import Service, ServiceCreate, ServiceUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Service])
def get_services(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search services by name (case-insensitive)"
    ),
    service_type_id: int | None = Query(
        None, description="Filter services by service type ID"
    ),
    db: Session = Depends(get_db),
):
    """Get all services with pagination, optional search, and service_type_id filter."""
    services, total = service.get_services(
        db=db, pagination=pagination, search=search, service_type_id=service_type_id
    )
    return create_paginated_result(services, total, pagination)


@router.get("/{service_id}", response_model=Service)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get a specific service by ID."""
    db_service = service.get_service(db, service_id)
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return db_service


@router.post("/", response_model=Service, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db)):
    """Create a new service."""
    try:
        return service.create_service(db, service_data)
    except ServiceAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidServiceTypeId as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{service_id}", response_model=Service)
def patch_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing service."""
    try:
        patched_service = service.patch_service(db, service_id, service_update)
        if not patched_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )
        return patched_service
    except ServiceAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidServiceTypeId as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Delete a service."""
    if not service.delete_service(db, service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
