from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.hierarchies.exceptions import (
    CircularReferenceError,
    DuplicateHierarchyName,
    HierarchyHasChildren,
    HierarchyHasPurposes,
    HierarchyNotFound,
    ParentHierarchyNotFound,
    SelfParentError,
)
from app.hierarchies.models import Hierarchy
from app.hierarchies.schemas import HierarchyCreate, HierarchyUpdate
from app.pagination import PaginationParams, paginate_select


def _calculate_path(db: Session, parent_id: int | None, name: str) -> str:
    """Calculate the full path for a hierarchy based on its parent."""
    if parent_id is None:
        return name

    stmt = select(Hierarchy).where(Hierarchy.id == parent_id)
    parent = db.execute(stmt).scalars().first()
    if not parent:
        return name

    return f"{parent.path} / {name}" if parent.path else name


def _update_children_paths(db: Session, hierarchy_id: int, new_path: str) -> None:
    """Recursively update paths for all children of a hierarchy."""
    stmt = select(Hierarchy).where(Hierarchy.parent_id == hierarchy_id)
    children = db.execute(stmt).scalars().all()

    for child in children:
        child.path = f"{new_path} / {child.name}"
        db.add(child)
        _update_children_paths(db, child.id, child.path)


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
    stmt = select(Hierarchy)

    # Apply filters
    if type_filter:
        stmt = stmt.where(Hierarchy.type == type_filter)

    if parent_id is not None:
        stmt = stmt.where(Hierarchy.parent_id == parent_id)

    if search:
        search_filter = f"%{search.lower()}%"
        stmt = stmt.where(func.lower(Hierarchy.name).like(search_filter))

    # Apply sorting
    sort_column = getattr(Hierarchy, sort_by, Hierarchy.name)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Apply pagination
    return paginate_select(db, stmt, pagination)


def get_hierarchy_by_id(db: Session, hierarchy_id: int) -> Hierarchy:
    """Get a hierarchy by ID."""
    stmt = select(Hierarchy).where(Hierarchy.id == hierarchy_id)
    hierarchy = db.execute(stmt).scalars().first()
    if not hierarchy:
        raise HierarchyNotFound(hierarchy_id)
    return hierarchy


def get_hierarchy_tree(db: Session, hierarchy_id: int | None = None) -> list[Hierarchy]:
    """Get hierarchy tree structure."""
    if hierarchy_id:
        # Get specific hierarchy and its children
        hierarchy = get_hierarchy_by_id(db, hierarchy_id)
        return _build_hierarchy_tree(db, hierarchy.id)
    else:
        # Get all root hierarchies (parent_id is None) with their children
        stmt = (
            select(Hierarchy)
            .where(Hierarchy.parent_id.is_(None))
            .options(selectinload(Hierarchy.children))
        )
        root_hierarchies = db.execute(stmt).scalars().all()

        # Build complete tree for each root
        for root in root_hierarchies:
            root.children = _build_hierarchy_tree(db, root.id)

        return root_hierarchies


def _build_hierarchy_tree(db: Session, parent_id: int) -> list[Hierarchy]:
    """Recursively build hierarchy tree."""
    stmt = (
        select(Hierarchy)
        .where(Hierarchy.parent_id == parent_id)
        .options(selectinload(Hierarchy.children))
    )
    hierarchies = db.execute(stmt).scalars().all()

    for hierarchy in hierarchies:
        hierarchy.children = _build_hierarchy_tree(db, hierarchy.id)

    return hierarchies


def create_hierarchy(db: Session, hierarchy_data: HierarchyCreate) -> Hierarchy:
    """Create a new hierarchy."""
    # Validate parent exists if parent_id is provided
    if hierarchy_data.parent_id:
        stmt = select(Hierarchy).where(Hierarchy.id == hierarchy_data.parent_id)
        parent = db.execute(stmt).scalars().first()
        if not parent:
            raise ParentHierarchyNotFound(hierarchy_data.parent_id)

    # Check for duplicate name within the same parent
    stmt = select(Hierarchy).where(
        and_(
            Hierarchy.name == hierarchy_data.name,
            Hierarchy.parent_id == hierarchy_data.parent_id,
        )
    )
    existing = db.execute(stmt).scalars().first()

    if existing:
        raise DuplicateHierarchyName(hierarchy_data.name)

    # Calculate path
    path = _calculate_path(db, hierarchy_data.parent_id, hierarchy_data.name)

    hierarchy = Hierarchy(**hierarchy_data.model_dump(), path=path)
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
            raise SelfParentError()

        # Check if the new parent would create a circular reference
        if _would_create_circular_reference(db, hierarchy_id, update_data["parent_id"]):
            raise CircularReferenceError()

        stmt = select(Hierarchy).where(Hierarchy.id == update_data["parent_id"])
        parent = db.execute(stmt).scalars().first()
        if not parent:
            raise ParentHierarchyNotFound(update_data["parent_id"])

    # Check for duplicate name if name is being updated
    if "name" in update_data:
        parent_id = update_data.get("parent_id", hierarchy.parent_id)
        stmt = select(Hierarchy).where(
            and_(
                Hierarchy.name == update_data["name"],
                Hierarchy.parent_id == parent_id,
                Hierarchy.id != hierarchy_id,
            )
        )
        existing = db.execute(stmt).scalars().first()

        if existing:
            raise DuplicateHierarchyName(update_data["name"])

    # Apply updates
    for field, value in update_data.items():
        setattr(hierarchy, field, value)

    # Recalculate path if parent_id or name changed
    if "parent_id" in update_data or "name" in update_data:
        new_name = update_data.get("name", hierarchy.name)
        new_parent_id = update_data.get("parent_id", hierarchy.parent_id)
        new_path = _calculate_path(db, new_parent_id, new_name)
        hierarchy.path = new_path

        # Update paths for all children
        _update_children_paths(db, hierarchy_id, new_path)

    db.commit()
    db.refresh(hierarchy)
    return hierarchy


def delete_hierarchy(db: Session, hierarchy_id: int) -> None:
    """Delete a hierarchy."""
    hierarchy = get_hierarchy_by_id(db, hierarchy_id)

    # Check if hierarchy has children
    stmt = select(func.count(Hierarchy.id)).where(Hierarchy.parent_id == hierarchy_id)
    children_count = db.execute(stmt).scalar()

    if children_count > 0:
        raise HierarchyHasChildren(children_count)

    # Check if hierarchy has associated purposes
    from app.purposes.models import Purpose

    stmt = select(func.count(Purpose.id)).where(Purpose.hierarchy_id == hierarchy_id)
    purposes_count = db.execute(stmt).scalar()
    if purposes_count > 0:
        raise HierarchyHasPurposes(purposes_count)

    db.delete(hierarchy)
    db.commit()


def _would_create_circular_reference(
    db: Session, hierarchy_id: int, new_parent_id: int
) -> bool:
    """Check if setting new_parent_id as parent would create a circular reference."""
    current_parent_id = new_parent_id
    visited = {hierarchy_id}

    while current_parent_id:
        if current_parent_id in visited:
            return True
        visited.add(current_parent_id)

        stmt = select(Hierarchy).where(Hierarchy.id == current_parent_id)
        parent = db.execute(stmt).scalars().first()
        if not parent:
            break
        current_parent_id = parent.parent_id

    return False
