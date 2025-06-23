from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as statuses
from sqlalchemy.orm import Session

from app.database import get_db
from app.hierarchies import service
from app.hierarchies.exceptions import (
    CircularReferenceError,
    DuplicateHierarchyName,
    HierarchyHasChildren,
    HierarchyHasPurposes,
    HierarchyNotFound,
    ParentHierarchyNotFound,
    SelfParentError,
)
from app.hierarchies.models import HierarchyTypeEnum
from app.hierarchies.schemas import (
    Hierarchy,
    HierarchyCreate,
    HierarchyTree,
    HierarchyUpdate,
)
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Hierarchy])
def get_hierarchies(
    pagination: PaginationParams = Depends(),
    type_filter: HierarchyTypeEnum | None = Query(None, description="Filter by type"),
    parent_id: int | None = Query(None, description="Filter by parent ID"),
    search: str | None = Query(None, description="Search in name"),
    sort_by: str = Query("name", description="Sort by field"),
    sort_order: Literal["asc", "desc"] = Query(
        "asc", description="Sort order: asc or desc"
    ),
    db: Session = Depends(get_db),
):
    """Get all hierarchies with filtering, searching, sorting, and pagination."""
    hierarchies, total = service.get_hierarchies(
        db=db,
        pagination=pagination,
        type_filter=type_filter.value if type_filter else None,
        parent_id=parent_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return create_paginated_result(hierarchies, total, pagination)


@router.get("/tree", response_model=list[HierarchyTree])
def get_hierarchy_tree(
    hierarchy_id: int | None = Query(
        None, description="Get tree for specific hierarchy"
    ),
    db: Session = Depends(get_db),
):
    """Get hierarchy tree structure."""
    try:
        return service.get_hierarchy_tree(db, hierarchy_id)
    except HierarchyNotFound as e:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get("/{hierarchy_id}", response_model=Hierarchy)
def get_hierarchy(hierarchy_id: int, db: Session = Depends(get_db)):
    """Get a specific hierarchy by ID."""
    try:
        return service.get_hierarchy_by_id(db, hierarchy_id)
    except HierarchyNotFound as e:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get("/{hierarchy_id}/children", response_model=list[Hierarchy])
def get_hierarchy_children(
    hierarchy_id: int,
    limit: int = Query(
        200, ge=1, le=1000, description="Maximum number of children to return"
    ),
    db: Session = Depends(get_db),
):
    """Get direct children of a hierarchy."""
    try:
        service.get_hierarchy_by_id(db, hierarchy_id)  # Validate hierarchy exists
        hierarchies, _ = service.get_hierarchies(
            db=db,
            pagination=PaginationParams(page=1, limit=limit),
            parent_id=hierarchy_id,
        )
        return hierarchies
    except HierarchyNotFound as e:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.post("/", response_model=Hierarchy, status_code=statuses.HTTP_201_CREATED)
def create_hierarchy(hierarchy_data: HierarchyCreate, db: Session = Depends(get_db)):
    """Create a new hierarchy."""
    try:
        return service.create_hierarchy(db, hierarchy_data)
    except (
        ParentHierarchyNotFound,
        DuplicateHierarchyName,
    ) as e:
        raise HTTPException(
            status_code=statuses.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.patch("/{hierarchy_id}", response_model=Hierarchy)
def update_hierarchy(
    hierarchy_id: int, hierarchy_data: HierarchyUpdate, db: Session = Depends(get_db)
):
    """Update an existing hierarchy."""
    try:
        return service.update_hierarchy(db, hierarchy_id, hierarchy_data)
    except HierarchyNotFound as e:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (
        ParentHierarchyNotFound,
        DuplicateHierarchyName,
        CircularReferenceError,
        SelfParentError,
    ) as e:
        raise HTTPException(
            status_code=statuses.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete("/{hierarchy_id}", status_code=statuses.HTTP_204_NO_CONTENT)
def delete_hierarchy(hierarchy_id: int, db: Session = Depends(get_db)):
    """Delete a hierarchy."""
    try:
        service.delete_hierarchy(db, hierarchy_id)
    except HierarchyNotFound as e:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (
        HierarchyHasChildren,
        HierarchyHasPurposes,
    ) as e:
        raise HTTPException(
            status_code=statuses.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
