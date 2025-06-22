from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pagination import PaginationParams, paginate
from app.service_types.models import ServiceType
from app.services.exceptions import InvalidServiceTypeId, ServiceAlreadyExists
from app.services.models import Service
from app.services.schemas import ServiceCreate, ServiceUpdate


def get_service(db: Session, service_id: int) -> Service | None:
    """Get a single service by ID."""
    return db.query(Service).filter(Service.id == service_id).first()


def get_services(
    db: Session,
    pagination: PaginationParams,
    search: str | None = None,
    service_type_id: int | None = None,
) -> tuple[list[Service], int]:
    """
    Get services with pagination and optional search and filtering.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for service name (case-insensitive)
        service_type_id: Optional filter by service type ID

    Returns:
        Tuple of (services list, total count)
    """
    query = db.query(Service)

    # Apply service_type_id filter if provided
    if service_type_id is not None:
        query = query.filter(Service.service_type_id == service_type_id)

    # Apply search filter if provided
    if search:
        query = query.filter(Service.name.ilike(f"%{search}%"))

    # Apply ordering
    query = query.order_by(Service.name)

    return paginate(query, pagination)


def create_service(db: Session, service: ServiceCreate) -> Service:
    """Create a new service."""
    # Validate that service_type_id exists
    service_type = (
        db.query(ServiceType).filter(ServiceType.id == service.service_type_id).first()
    )
    if not service_type:
        raise InvalidServiceTypeId(
            f"Service type with ID {service.service_type_id} does not exist"
        )

    try:
        db_service = Service(**service.model_dump())
        db.add(db_service)
        db.commit()
        db.refresh(db_service)
        return db_service
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e) and "service" in str(e):
            raise ServiceAlreadyExists(
                f"Service '{service.name}' already exists for this service type"
            )
        raise


def patch_service(
    db: Session, service_id: int, service_update: ServiceUpdate
) -> Service | None:
    """Patch an existing service."""
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        return None

    # Validate service_type_id if it's being updated
    update_data = service_update.model_dump(exclude_unset=True)
    if "service_type_id" in update_data and update_data["service_type_id"] is not None:
        service_type = (
            db.query(ServiceType)
            .filter(ServiceType.id == update_data["service_type_id"])
            .first()
        )
        if not service_type:
            raise InvalidServiceTypeId(
                f"Service type with ID {update_data['service_type_id']} does not exist"
            )

    try:
        for field, value in update_data.items():
            if value is not None:
                setattr(db_service, field, value)

        db.commit()
        db.refresh(db_service)
        return db_service
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e) and "service" in str(e):
            raise ServiceAlreadyExists(
                f"Service '{service_update.name}' already exists for this service type"
            )
        raise


def delete_service(db: Session, service_id: int) -> bool:
    """Delete a service. Returns True if deleted, False if not found."""
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        return False

    db.delete(db_service)
    db.commit()
    return True
