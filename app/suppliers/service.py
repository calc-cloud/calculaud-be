from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate
from app.suppliers.exceptions import SupplierAlreadyExists
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
    try:
        db_supplier = Supplier(**supplier.model_dump())
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e) and "supplier" in str(e):
            raise SupplierAlreadyExists(f"Supplier '{supplier.name}' already exists")
        raise


def patch_supplier(
    db: Session, supplier_id: int, supplier_update: SupplierUpdate
) -> Supplier | None:
    """Patch an existing supplier."""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        return None

    try:
        for field, value in supplier_update.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(db_supplier, field, value)

        db.commit()
        db.refresh(db_supplier)
        return db_supplier
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e) and "supplier" in str(e):
            raise SupplierAlreadyExists(
                f"Supplier '{supplier_update.name}' already exists"
            )
        raise


def delete_supplier(db: Session, supplier_id: int) -> bool:
    """Delete a supplier. Returns True if deleted, False if not found."""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not db_supplier:
        return False

    db.delete(db_supplier)
    db.commit()
    return True
