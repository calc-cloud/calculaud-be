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
        None,
        description=(
            "Search suppliers by name (not case-sensitive). "
            "Examples: 'Google' matches 'Google LLC', 'Microsoft Corp', 'ABC-123'. "
            "Supports company names, abbreviations, and alphanumeric codes. "
            "Leave empty to retrieve all suppliers. "
            "Special characters are allowed. Minimum 1 character when provided."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve suppliers from the procurement system with advanced filtering and pagination.

    **Purpose**: Search and list supplier companies registered in the procurement system.
    Use this function to find specific suppliers by name or retrieve all available suppliers.

    **When to use this function**:
    - User asks for suppliers: "show me suppliers", "list suppliers", "find suppliers"
    - Searching by company name: "find Google suppliers", "search for Microsoft"
    - Getting all suppliers: "get all suppliers", "list all companies"
    - Browsing supplier directory with pagination

    **Parameters**:
    - **search** (optional): Company name search term
      - Format: Any string, partial matching supported
      - Examples: "Google" → matches "Google LLC", "Google Inc"
      - Examples: "Corp" → matches "Microsoft Corp", "ABC Corp"
      - Case-sensitive: "google" does NOT match "Google LLC", use exact case
      - Empty/null: Returns all suppliers
      - Edge cases: Special characters allowed, single character searches supported

    - **pagination**: Standard pagination with page/limit
      - Default: page=1, limit=100
      - Maximum limit: 1000 items per page

    **Response Format**:
    - **items**: Array of supplier objects with id, name, file_icon
    - **total**: Total count of matching suppliers
    - **page/limit**: Current pagination parameters
    - **has_next/has_prev**: Navigation flags

    **Example Responses**:
    - Search "Google": Returns suppliers with names containing "Google"
    - Empty search: Returns all suppliers (paginated)
    - No matches: Returns empty items array with total=0

    **Edge Cases**:
    - Invalid page numbers: Returns empty results
    - Search too broad: Results are paginated automatically
    - No suppliers exist: Returns empty array with total=0
    - Database unavailable: Raises 500 error

    **Business Context**:
    Suppliers are companies/vendors in the procurement system that provide
    goods and services. Each supplier has a unique name and optional icon attachment.
    """
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
