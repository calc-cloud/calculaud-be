from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.files.models import FileAttachment
from app.pagination import PaginationParams, paginate_select
from app.suppliers.exceptions import (
    InvalidFileIcon,
    SupplierAlreadyExists,
    SupplierNotFound,
)
from app.suppliers.models import Supplier
from app.suppliers.schemas import SupplierCreate, SupplierUpdate


def get_supplier(db: Session, supplier_id: int) -> Supplier | None:
    """Get a single supplier by ID."""
    stmt = (
        select(Supplier)
        .options(joinedload(Supplier.file_icon))
        .where(Supplier.id == supplier_id)
    )
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
    stmt = select(Supplier).options(joinedload(Supplier.file_icon))

    # Apply search filter if provided
    if search:
        stmt = stmt.where(Supplier.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(Supplier.name)

    return paginate_select(db, stmt, pagination)


def _validate_file_icon(db: Session, file_icon_id: int | None) -> None:
    """Validate that file_icon_id exists if provided."""
    if file_icon_id is not None:
        stmt = select(FileAttachment).where(FileAttachment.id == file_icon_id)
        file_attachment = db.execute(stmt).scalar_one_or_none()
        if not file_attachment:
            raise InvalidFileIcon(f"File with ID {file_icon_id} not found")


def create_supplier(db: Session, supplier: SupplierCreate) -> Supplier:
    """Create a new supplier."""
    # Check if supplier with this name already exists
    stmt = select(Supplier).where(Supplier.name == supplier.name)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise SupplierAlreadyExists(f"Supplier '{supplier.name}' already exists")

    # Validate file icon if provided
    _validate_file_icon(db, supplier.file_icon_id)

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

    # Validate file icon if being updated
    if "file_icon_id" in update_data:
        _validate_file_icon(db, update_data["file_icon_id"])

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
