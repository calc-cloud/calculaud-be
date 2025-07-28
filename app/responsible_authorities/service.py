from sqlalchemy import select
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate_select
from app.responsible_authorities.exceptions import (
    ResponsibleAuthorityAlreadyExists,
    ResponsibleAuthorityNotFound,
)
from app.responsible_authorities.models import ResponsibleAuthority
from app.responsible_authorities.schemas import (
    ResponsibleAuthorityCreate,
    ResponsibleAuthorityUpdate,
)


def get_responsible_authority(
    db: Session, authority_id: int
) -> ResponsibleAuthority | None:
    """Get a single responsible authority by ID."""
    stmt = select(ResponsibleAuthority).where(ResponsibleAuthority.id == authority_id)
    return db.execute(stmt).scalars().first()


def get_responsible_authorities(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[ResponsibleAuthority], int]:
    """
    Get responsible authorities with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for authority name (case-insensitive)

    Returns:
        Tuple of (authorities list, total count)
    """
    stmt = select(ResponsibleAuthority)

    # Apply search filter if provided
    if search:
        stmt = stmt.where(ResponsibleAuthority.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(ResponsibleAuthority.name)

    return paginate_select(db, stmt, pagination)


def create_responsible_authority(
    db: Session, authority: ResponsibleAuthorityCreate
) -> ResponsibleAuthority:
    """Create a new responsible authority."""
    # Check if authority with this name already exists
    stmt = select(ResponsibleAuthority).where(
        ResponsibleAuthority.name == authority.name
    )
    existing = db.execute(stmt).scalars().first()
    if existing:
        raise ResponsibleAuthorityAlreadyExists(authority.name)

    db_authority = ResponsibleAuthority(**authority.model_dump())
    db.add(db_authority)
    db.commit()
    db.refresh(db_authority)
    return db_authority


def patch_responsible_authority(
    db: Session, authority_id: int, authority_update: ResponsibleAuthorityUpdate
) -> ResponsibleAuthority:
    """Patch an existing responsible authority."""
    stmt = select(ResponsibleAuthority).where(ResponsibleAuthority.id == authority_id)
    db_authority = db.execute(stmt).scalars().first()
    if not db_authority:
        raise ResponsibleAuthorityNotFound(authority_id)

    update_data = authority_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        stmt = (
            select(ResponsibleAuthority)
            .where(ResponsibleAuthority.name == update_data["name"])
            .where(ResponsibleAuthority.id != authority_id)
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            raise ResponsibleAuthorityAlreadyExists(update_data["name"])

    for field, value in update_data.items():
        if value is not None:
            setattr(db_authority, field, value)

    db.commit()
    db.refresh(db_authority)
    return db_authority


def delete_responsible_authority(db: Session, authority_id: int) -> None:
    """Delete a responsible authority."""
    stmt = select(ResponsibleAuthority).where(ResponsibleAuthority.id == authority_id)
    db_authority = db.execute(stmt).scalars().first()
    if not db_authority:
        raise ResponsibleAuthorityNotFound(authority_id)

    db.delete(db_authority)
    db.commit()
