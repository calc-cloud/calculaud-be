from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from app.hierarchies.models import Hierarchy
from app.hierarchies.schemas import HierarchyCreate, HierarchyUpdate
from app.pagination import PaginationParams, paginate


def get_hierarchies(
    db: Session,
    pagination: PaginationParams,
    type_filter: str | None = None,
    parent_id: int | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
) -> tuple[list[Hierarchy], int]:
    """Get hierarchies with filtering, searching, sorting, and pagination."""
    query = db.query(Hierarchy)

    # Apply filters
    if type_filter:
        query = query.filter(Hierarchy.type == type_filter)

    if parent_id is not None:
        query = query.filter(Hierarchy.parent_id == parent_id)

    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(func.lower(Hierarchy.name).like(search_filter))

    # Apply sorting
    sort_column = getattr(Hierarchy, sort_by, Hierarchy.name)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    return paginate(query, pagination)


def get_hierarchy_by_id(db: Session, hierarchy_id: int) -> Hierarchy:
    """Get a hierarchy by ID."""
    hierarchy = db.query(Hierarchy).filter(Hierarchy.id == hierarchy_id).first()
    if not hierarchy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hierarchy with id {hierarchy_id} not found",
        )
    return hierarchy


def get_hierarchy_tree(db: Session, hierarchy_id: int | None = None) -> list[Hierarchy]:
    """Get hierarchy tree structure."""
    if hierarchy_id:
        # Get specific hierarchy and its children
        hierarchy = get_hierarchy_by_id(db, hierarchy_id)
        return _build_hierarchy_tree(db, hierarchy.id)
    else:
        # Get all root hierarchies (parent_id is None)
        root_hierarchies = (
            db.query(Hierarchy)
            .filter(Hierarchy.parent_id.is_(None))
            .options(selectinload(Hierarchy.children))
            .all()
        )
        result = []
        for root in root_hierarchies:
            tree = _build_hierarchy_tree(db, root.id)
            result.extend(tree)
        return result


def _build_hierarchy_tree(db: Session, parent_id: int) -> list[Hierarchy]:
    """Recursively build hierarchy tree."""
    hierarchies = (
        db.query(Hierarchy)
        .filter(Hierarchy.parent_id == parent_id)
        .options(selectinload(Hierarchy.children))
        .all()
    )

    for hierarchy in hierarchies:
        hierarchy.children = _build_hierarchy_tree(db, hierarchy.id)

    return hierarchies


def create_hierarchy(db: Session, hierarchy_data: HierarchyCreate) -> Hierarchy:
    """Create a new hierarchy."""
    # Validate parent exists if parent_id is provided
    if hierarchy_data.parent_id:
        parent = (
            db.query(Hierarchy).filter(Hierarchy.id == hierarchy_data.parent_id).first()
        )
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent hierarchy with id {hierarchy_data.parent_id} not found",
            )

    # Check for duplicate name within the same parent
    existing = (
        db.query(Hierarchy)
        .filter(
            and_(
                Hierarchy.name == hierarchy_data.name,
                Hierarchy.parent_id == hierarchy_data.parent_id,
            )
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hierarchy with name '{hierarchy_data.name}' already exists under the same parent",
        )

    hierarchy = Hierarchy(**hierarchy_data.model_dump())
    db.add(hierarchy)
    db.commit()
    db.refresh(hierarchy)
    return hierarchy


def update_hierarchy(
    db: Session, hierarchy_id: int, hierarchy_data: HierarchyUpdate
) -> Hierarchy:
    """Update an existing hierarchy."""
    hierarchy = get_hierarchy_by_id(db, hierarchy_id)

    # Prepare update data, excluding None values
    update_data = hierarchy_data.model_dump(exclude_unset=True)

    # Validate parent exists if parent_id is being updated
    if "parent_id" in update_data and update_data["parent_id"]:
        # Check for circular reference
        if update_data["parent_id"] == hierarchy_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A hierarchy cannot be its own parent",
            )

        # Check if the new parent would create a circular reference
        if _would_create_circular_reference(db, hierarchy_id, update_data["parent_id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This parent assignment would create a circular reference",
            )

        parent = (
            db.query(Hierarchy).filter(Hierarchy.id == update_data["parent_id"]).first()
        )
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent hierarchy with id {update_data['parent_id']} not found",
            )

    # Check for duplicate name if name is being updated
    if "name" in update_data:
        parent_id = update_data.get("parent_id", hierarchy.parent_id)
        existing = (
            db.query(Hierarchy)
            .filter(
                and_(
                    Hierarchy.name == update_data["name"],
                    Hierarchy.parent_id == parent_id,
                    Hierarchy.id != hierarchy_id,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hierarchy with name '{update_data['name']}' already exists under the same parent",
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(hierarchy, field, value)

    db.commit()
    db.refresh(hierarchy)
    return hierarchy


def delete_hierarchy(db: Session, hierarchy_id: int) -> None:
    """Delete a hierarchy."""
    hierarchy = get_hierarchy_by_id(db, hierarchy_id)

    # Check if hierarchy has children
    children_count = (
        db.query(Hierarchy).filter(Hierarchy.parent_id == hierarchy_id).count()
    )
    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete hierarchy that has children. Delete children first or reassign them.",
        )

    # Check if hierarchy has associated purposes
    from app.purposes.models import Purpose

    purposes_count = (
        db.query(Purpose).filter(Purpose.hierarchy_id == hierarchy_id).count()
    )
    if purposes_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete hierarchy that has associated purposes. Reassign purposes first.",
        )

    db.delete(hierarchy)
    db.commit()


def _would_create_circular_reference(
    db: Session, hierarchy_id: int, new_parent_id: int
) -> bool:
    """Check if setting new_parent_id as parent would create a circular reference."""
    # Walk up the tree from new_parent_id to see if we encounter hierarchy_id
    current_id = new_parent_id
    visited = set()

    while current_id and current_id not in visited:
        if current_id == hierarchy_id:
            return True
        visited.add(current_id)

        parent = db.query(Hierarchy).filter(Hierarchy.id == current_id).first()
        current_id = parent.parent_id if parent else None

    return False
