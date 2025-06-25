from sqlalchemy import select
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate_select
from app.suppliers.exceptions import SupplierAlreadyExists, SupplierNotFound
from app.suppliers.models import Supplier
from app.suppliers.schemas import SupplierCreate, SupplierUpdate


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    """Get a single supplier by ID."""
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    return db.execute(stmt).scalar_one_or_none()


def get_suppliers(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[Supplier], int]:
    """
    Get suppliers with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for supplier name (case-insensitive)

    Returns:
        Tuple of (suppliers list, total count)
    """
    stmt = select(Supplier)

    # Apply search filter if provided
    if search:
        stmt = stmt.where(Supplier.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(Supplier.name)

    return paginate_select(db, stmt, pagination)


def create_supplier(db: Session, supplier: SupplierCreate) -> Supplier:
    """Create a new supplier."""
    # Check if supplier with this name already exists
    stmt = select(Supplier).where(Supplier.name == supplier.name)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise SupplierAlreadyExists(f"Supplier '{supplier.name}' already exists")

    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def patch_supplier(
    db: Session, supplier_id: int, supplier_update: SupplierUpdate
) -> Supplier:
    """Patch an existing supplier."""
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    db_supplier = db.execute(stmt).scalar_one_or_none()
    if not db_supplier:
        raise SupplierNotFound(f"Supplier with ID {supplier_id} not found")

    update_data = supplier_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        existing_stmt = (
            select(Supplier)
            .where(Supplier.name == update_data["name"])
            .where(Supplier.id != supplier_id)
        )
        existing = db.execute(existing_stmt).scalar_one_or_none()
        if existing:
            raise SupplierAlreadyExists(
                f"Supplier '{update_data['name']}' already exists"
            )

    for field, value in update_data.items():
        if value is not None:
            setattr(db_supplier, field, value)

    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: int) -> None:
    """Delete a supplier."""
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    db_supplier = db.execute(stmt).scalar_one_or_none()
    if not db_supplier:
        raise SupplierNotFound(f"Supplier with ID {supplier_id} not found")

    db.delete(db_supplier)
    db.commit()
