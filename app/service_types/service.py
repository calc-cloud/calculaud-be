from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate
from app.service_types.exceptions import ServiceTypeAlreadyExists
from app.service_types.models import ServiceType
from app.service_types.schemas import ServiceTypeCreate, ServiceTypeUpdate


def get_service_type(db: Session, service_type_id: int) -> ServiceType | None:
    """Get a single service type by ID."""
    return db.query(ServiceType).filter(ServiceType.id == service_type_id).first()


def get_service_types(
    db: Session, pagination: PaginationParams
) -> tuple[list[ServiceType], int]:
    """
    Get service types with pagination.

    Returns:
        Tuple of (service_types list, total count)
    """
    query = db.query(ServiceType).order_by(ServiceType.name)
    return paginate(query, pagination)


def create_service_type(db: Session, service_type: ServiceTypeCreate) -> ServiceType:
    """Create a new service type."""
    try:
        db_service_type = ServiceType(**service_type.model_dump())
        db.add(db_service_type)
        db.commit()
        db.refresh(db_service_type)
        return db_service_type
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e) and "service_type" in str(e):
            raise ServiceTypeAlreadyExists(f"Service type '{service_type.name}' already exists")
        raise


def patch_service_type(
    db: Session, service_type_id: int, service_type_update: ServiceTypeUpdate
) -> ServiceType | None:
    """Patch an existing service type."""
    db_service_type = (
        db.query(ServiceType).filter(ServiceType.id == service_type_id).first()
    )
    if not db_service_type:
        return None

    try:
        for field, value in service_type_update.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(db_service_type, field, value)

        db.commit()
        db.refresh(db_service_type)
        return db_service_type
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e) and "service_type" in str(e):
            raise ServiceTypeAlreadyExists(f"Service type '{service_type_update.name}' already exists")
        raise


def delete_service_type(db: Session, service_type_id: int) -> bool:
    """Delete a service type. Returns True if deleted, False if not found."""
    db_service_type = (
        db.query(ServiceType).filter(ServiceType.id == service_type_id).first()
    )
    if not db_service_type:
        return False

    db.delete(db_service_type)
    db.commit()
    return True
