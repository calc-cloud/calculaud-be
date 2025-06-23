from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate
from app.suppliers.exceptions import SupplierAlreadyExists, SupplierNotFound
from app.suppliers.models import Supplier
from app.suppliers.schemas import SupplierCreate, SupplierUpdate


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    """Get a single supplier by ID."""
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()


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
    query = db.query(Supplier)

    # Apply search filter if provided
    if search:
        query = query.filter(Supplier.name.ilike(f"%{search}%"))

    # Apply ordering
    query = query.order_by(Supplier.name)

    return paginate(query, pagination)


def create_supplier(db: Session, supplier: SupplierCreate) -> Supplier:
    """Create a new supplier."""
    # Check if supplier with this name already exists
    existing = db.query(Supplier).filter(Supplier.name == supplier.name).first()
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
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise SupplierNotFound(f"Supplier with ID {supplier_id} not found")

    update_data = supplier_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        existing = (
            db.query(Supplier)
            .filter(Supplier.name == update_data["name"])
            .filter(Supplier.id != supplier_id)
            .first()
        )
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
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        raise SupplierNotFound(f"Supplier with ID {supplier_id} not found")

    db.delete(db_supplier)
    db.commit()
