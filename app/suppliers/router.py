from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.suppliers import service
from app.suppliers.exceptions import (
    InvalidFileIcon,
    SupplierAlreadyExists,
    SupplierNotFound,
)
from app.suppliers.schemas import Supplier, SupplierCreate, SupplierUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Supplier], operation_id="get_suppliers")
def get_suppliers(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search suppliers by name (case-insensitive)"
    ),
    db: Session = Depends(get_db),
):
    """Get all suppliers with pagination and optional search."""
    suppliers, total = service.get_suppliers(
        db=db, pagination=pagination, search=search
    )
    return create_paginated_result(suppliers, total, pagination)


@router.get("/{supplier_id}", response_model=Supplier, operation_id="get_supplier")
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Get a specific supplier by ID."""
    supplier = service.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )
    return supplier


@router.post("/", response_model=Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    """Create a new supplier."""
    try:
        return service.create_supplier(db, supplier)
    except SupplierAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except InvalidFileIcon as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.patch("/{supplier_id}", response_model=Supplier)
def patch_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing supplier."""
    try:
        return service.patch_supplier(db, supplier_id, supplier_update)
    except SupplierNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except SupplierAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except InvalidFileIcon as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Delete a supplier."""
    try:
        service.delete_supplier(db, supplier_id)
    except SupplierNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
