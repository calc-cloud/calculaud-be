from sqlalchemy import select
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate_select
from app.stage_types.exceptions import StageTypeAlreadyExists, StageTypeNotFound
from app.stage_types.models import StageType
from app.stage_types.schemas import StageTypeCreate, StageTypeUpdate


def get_stage_type(db: Session, stage_type_id: int) -> StageType | None:
    """Get a single stage type by ID."""
    stmt = select(StageType).where(StageType.id == stage_type_id)
    return db.execute(stmt).scalars().first()


def get_stage_types(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[StageType], int]:
    """
    Get stage types with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for stage type name (case-insensitive)

    Returns:
        Tuple of (stage_types list, total count)
    """
    stmt = select(StageType)

    # Apply search filter if provided
    if search:
        stmt = stmt.where(StageType.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(StageType.name)

    return paginate_select(db, stmt, pagination)


def create_stage_type(db: Session, stage_type: StageTypeCreate) -> StageType:
    """Create a new stage type."""
    # Check if stage type with this name already exists
    stmt = select(StageType).where(StageType.name == stage_type.name)
    existing = db.execute(stmt).scalars().first()
    if existing:
        raise StageTypeAlreadyExists(stage_type.name)

    db_stage_type = StageType(**stage_type.model_dump())
    db.add(db_stage_type)
    db.commit()
    db.refresh(db_stage_type)
    return db_stage_type


def patch_stage_type(
    db: Session, stage_type_id: int, stage_type_update: StageTypeUpdate
) -> StageType:
    """Patch an existing stage type."""
    stmt = select(StageType).where(StageType.id == stage_type_id)
    db_stage_type = db.execute(stmt).scalars().first()
    if not db_stage_type:
        raise StageTypeNotFound(stage_type_id)

    update_data = stage_type_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        stmt = (
            select(StageType)
            .where(StageType.name == update_data["name"])
            .where(StageType.id != stage_type_id)
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            raise StageTypeAlreadyExists(update_data["name"])

    for field, value in update_data.items():
        if value is not None:
            setattr(db_stage_type, field, value)

    db.commit()
    db.refresh(db_stage_type)
    return db_stage_type


def delete_stage_type(db: Session, stage_type_id: int) -> None:
    """Delete a stage type."""
    stmt = select(StageType).where(StageType.id == stage_type_id)
    db_stage_type = db.execute(stmt).scalars().first()
    if not db_stage_type:
        raise StageTypeNotFound(stage_type_id)

    db.delete(db_stage_type)
    db.commit()