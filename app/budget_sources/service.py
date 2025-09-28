from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budget_sources.exceptions import (
    BudgetSourceAlreadyExists,
    BudgetSourceNotFound,
)
from app.budget_sources.models import BudgetSource
from app.budget_sources.schemas import BudgetSourceCreate, BudgetSourceUpdate
from app.pagination import PaginationParams, paginate_select


def get_budget_source(db: Session, budget_source_id: int) -> BudgetSource | None:
    """Get a single budget source by ID."""
    stmt = select(BudgetSource).where(BudgetSource.id == budget_source_id)
    return db.execute(stmt).scalar_one_or_none()


def get_budget_sources(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[BudgetSource], int]:
    """
    Get budget sources with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for budget source name (case-insensitive)

    Returns:
        Tuple of (budget sources list, total count)
    """
    stmt = select(BudgetSource)

    # Apply search filter if provided
    if search:
        stmt = stmt.where(BudgetSource.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(BudgetSource.name)

    return paginate_select(db, stmt, pagination)


def create_budget_source(
    db: Session, budget_source: BudgetSourceCreate
) -> BudgetSource:
    """Create a new budget source."""
    # Check if budget source with this name already exists
    stmt = select(BudgetSource).where(BudgetSource.name == budget_source.name)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise BudgetSourceAlreadyExists(
            f"Budget source '{budget_source.name}' already exists"
        )

    db_budget_source = BudgetSource(**budget_source.model_dump())
    db.add(db_budget_source)
    db.commit()
    db.refresh(db_budget_source)
    return db_budget_source


def patch_budget_source(
    db: Session, budget_source_id: int, budget_source_update: BudgetSourceUpdate
) -> BudgetSource:
    """Patch an existing budget source."""
    stmt = select(BudgetSource).where(BudgetSource.id == budget_source_id)
    db_budget_source = db.execute(stmt).scalar_one_or_none()
    if not db_budget_source:
        raise BudgetSourceNotFound(
            f"Budget source with ID {budget_source_id} not found"
        )

    update_data = budget_source_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        existing_stmt = (
            select(BudgetSource)
            .where(BudgetSource.name == update_data["name"])
            .where(BudgetSource.id != budget_source_id)
        )
        existing = db.execute(existing_stmt).scalar_one_or_none()
        if existing:
            raise BudgetSourceAlreadyExists(
                f"Budget source '{update_data['name']}' already exists"
            )

    for field, value in update_data.items():
        setattr(db_budget_source, field, value)

    db.commit()
    db.refresh(db_budget_source)
    return db_budget_source


def delete_budget_source(db: Session, budget_source_id: int) -> None:
    """Delete a budget source."""
    stmt = select(BudgetSource).where(BudgetSource.id == budget_source_id)
    db_budget_source = db.execute(stmt).scalar_one_or_none()
    if not db_budget_source:
        raise BudgetSourceNotFound(
            f"Budget source with ID {budget_source_id} not found"
        )

    db.delete(db_budget_source)
    db.commit()
