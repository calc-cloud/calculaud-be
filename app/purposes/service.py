from typing import Literal

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.pagination import PaginationParams, paginate
from app.purposes.models import Purpose, StatusEnum
from app.purposes.schemas import PurposeCreate


def get_purpose(db: Session, purpose_id: int) -> Purpose | None:
    """Get a single purpose by ID."""
    return (
        db.query(Purpose)
        .options(joinedload(Purpose.emfs))
        .filter(Purpose.id == purpose_id)
        .first()
    )


def get_purposes(
    db: Session,
    pagination: PaginationParams,
    hierarchy_id: int | None = None,
    supplier: str | None = None,
    service_type: str | None = None,
    status: StatusEnum | None = None,
    search: str | None = None,
    sort_by: str = "creation_time",
    sort_order: Literal["asc", "desc"] = "desc",
) -> tuple[list[Purpose], int]:
    """
    Get purposes with filtering, searching, sorting, and pagination.
    
    Returns:
        Tuple of (purposes list, total count)
    """
    query = db.query(Purpose).options(joinedload(Purpose.emfs))

    # Apply filters
    filters = []
    if hierarchy_id is not None:
        filters.append(Purpose.hierarchy_id == hierarchy_id)
    if supplier:
        filters.append(Purpose.supplier.ilike(f"%{supplier}%"))
    if service_type:
        filters.append(Purpose.service_type.ilike(f"%{service_type}%"))
    if status:
        filters.append(Purpose.status == status)

    if filters:
        query = query.filter(and_(*filters))

    # Apply search
    if search:
        search_filter = or_(
            Purpose.description.ilike(f"%{search}%"),
            Purpose.content.ilike(f"%{search}%"),
            Purpose.supplier.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Apply sorting
    sort_column = getattr(Purpose, sort_by, Purpose.creation_time)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Apply pagination
    return paginate(query, pagination)


def create_purpose(db: Session, purpose: PurposeCreate) -> Purpose:
    """Create a new purpose."""
    db_purpose = Purpose(**purpose.model_dump())
    db.add(db_purpose)
    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def patch_purpose(
    db: Session, purpose_id: int, purpose_update: dict
) -> Purpose | None:
    """Patch an existing purpose."""
    db_purpose = db.query(Purpose).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return None

    for field, value in purpose_update.items():
        setattr(db_purpose, field, value)

    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def delete_purpose(db: Session, purpose_id: int) -> bool:
    """Delete a purpose. Returns True if deleted, False if not found."""
    db_purpose = db.query(Purpose).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return False

    db.delete(db_purpose)
    db.commit()
    return True