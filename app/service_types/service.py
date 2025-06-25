from sqlalchemy import select
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate_select
from app.service_types.exceptions import ServiceTypeAlreadyExists, ServiceTypeNotFound
from app.service_types.models import ServiceType
from app.service_types.schemas import ServiceTypeCreate, ServiceTypeUpdate


def get_service_type(db: Session, service_type_id: int) -> ServiceType | None:
    """Get a single service type by ID."""
    stmt = select(ServiceType).where(ServiceType.id == service_type_id)
    return db.execute(stmt).scalars().first()


def get_service_types(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[ServiceType], int]:
    """
    Get service types with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for service type name (case-insensitive)

    Returns:
        Tuple of (service_types list, total count)
    """
    stmt = select(ServiceType)

    # Apply search filter if provided
    if search:
        stmt = stmt.where(ServiceType.name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(ServiceType.name)

    return paginate_select(db, stmt, pagination)


def create_service_type(db: Session, service_type: ServiceTypeCreate) -> ServiceType:
    """Create a new service type."""
    # Check if service type with this name already exists
    stmt = select(ServiceType).where(ServiceType.name == service_type.name)
    existing = db.execute(stmt).scalars().first()
    if existing:
        raise ServiceTypeAlreadyExists(
            f"Service type '{service_type.name}' already exists"
        )

    db_service_type = ServiceType(**service_type.model_dump())
    db.add(db_service_type)
    db.commit()
    db.refresh(db_service_type)
    return db_service_type


def patch_service_type(
    db: Session, service_type_id: int, service_type_update: ServiceTypeUpdate
) -> ServiceType:
    """Patch an existing service type."""
    stmt = select(ServiceType).where(ServiceType.id == service_type_id)
    db_service_type = db.execute(stmt).scalars().first()
    if not db_service_type:
        raise ServiceTypeNotFound(f"Service type with ID {service_type_id} not found")

    update_data = service_type_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] is not None:
        stmt = (
            select(ServiceType)
            .where(ServiceType.name == update_data["name"])
            .where(ServiceType.id != service_type_id)
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            raise ServiceTypeAlreadyExists(
                f"Service type '{update_data['name']}' already exists"
            )

    for field, value in update_data.items():
        if value is not None:
            setattr(db_service_type, field, value)

    db.commit()
    db.refresh(db_service_type)
    return db_service_type


def delete_service_type(db: Session, service_type_id: int) -> None:
    """Delete a service type."""
    stmt = select(ServiceType).where(ServiceType.id == service_type_id)
    db_service_type = db.execute(stmt).scalars().first()
    if not db_service_type:
        raise ServiceTypeNotFound(f"Service type with ID {service_type_id} not found")

    db.delete(db_service_type)
    db.commit()
