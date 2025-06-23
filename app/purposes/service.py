from typing import Literal

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.common.hierarchy_utils import build_hierarchy_filter
from app.costs.models import Cost
from app.emfs.models import EMF
from app.files import service as file_service
from app.hierarchies.models import Hierarchy
from app.pagination import PaginationParams, paginate
from app.purposes.exceptions import DuplicateServiceInPurpose, ServiceNotFound
from app.purposes.models import Purpose, PurposeContent, StatusEnum
from app.purposes.schemas import PurposeContentBase, PurposeCreate, PurposeUpdate
from app.services.models import Service


def _get_base_purpose_query(db: Session):
    """Get base purpose query with all necessary joins."""
    return db.query(Purpose).options(
        joinedload(Purpose.emfs),
        joinedload(Purpose.file_attachments),
        joinedload(Purpose.contents)
        .joinedload(PurposeContent.service)
        .joinedload(Service.service_type),
    )


def _validate_service_exists(db: Session, service_id: int) -> None:
    """Validate that a service exists, raise ServiceNotFound if not."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise ServiceNotFound(service_id)


def _validate_unique_services_in_purpose(services: list[PurposeContentBase]) -> None:
    """Validate that all services in purpose contents are unique."""
    service_ids = [content.service_id for content in services]

    if len(service_ids) != len(set(service_ids)):
        # Find the duplicate service_id
        seen = set()
        for service_id in service_ids:
            if service_id in seen:
                raise DuplicateServiceInPurpose(service_id)
            seen.add(service_id)


def _create_purpose_content(
    db: Session, purpose_id: int, content_data
) -> PurposeContent:
    """Create a purpose content entry with validation."""
    _validate_service_exists(db, content_data.service_id)

    db_content = PurposeContent(
        purpose_id=purpose_id,
        service_id=content_data.service_id,
        quantity=content_data.quantity,
    )
    db.add(db_content)
    db.flush()
    return db_content


def _create_emf_with_costs(db: Session, purpose_id: int, emf_data) -> EMF:
    """Create an EMF with its associated costs."""
    emf_dict = emf_data.model_dump(exclude={"costs"})
    db_emf = EMF(**emf_dict, purpose_id=purpose_id)
    db.add(db_emf)
    db.flush()

    # Create costs for this EMF if provided
    for cost_data in emf_data.costs:
        db_cost = Cost(**cost_data.model_dump(), emf_id=db_emf.id)
        db.add(db_cost)

    return db_emf


def _update_existing_emf(db: Session, existing_emf: EMF, emf_data) -> None:
    """Update an existing EMF with new data."""
    emf_dict = emf_data.model_dump(exclude={"costs"})
    for field, value in emf_dict.items():
        if value is not None:
            setattr(existing_emf, field, value)

    # Update costs if provided
    if emf_data.costs is not None:
        # Clear existing costs and create new ones
        db.query(Cost).filter(Cost.emf_id == existing_emf.id).delete()
        for cost_data in emf_data.costs:
            db_cost = Cost(**cost_data.model_dump(), emf_id=existing_emf.id)
            db.add(db_cost)


def _build_basic_filters(
    service_type_id: list[int] | None,
    service_id: list[int] | None,
    supplier_id: list[int] | None,
    status: list[StatusEnum] | None,
) -> list:
    """Build basic filters for purpose queries."""
    filters = []

    if service_type_id:
        filters.append(Purpose.service_type_id.in_(service_type_id))

    if service_id:
        filters.append(Purpose.contents.any(PurposeContent.service_id.in_(service_id)))

    if supplier_id:
        filters.append(Purpose.supplier_id.in_(supplier_id))

    if  status:
        filters.append(Purpose.status.in_(status))

    return filters


def _build_search_filter(search: str):
    """Build search filter for purpose queries."""
    return or_(
        Purpose.description.ilike(f"%{search}%"),
        Purpose.emfs.any(EMF.emf_id.ilike(f"%{search}%")),
        Purpose.emfs.any(EMF.order_id.ilike(f"%{search}%")),
        Purpose.emfs.any(EMF.demand_id.ilike(f"%{search}%")),
        Purpose.emfs.any(EMF.bikushit_id.ilike(f"%{search}%")),
        Purpose.contents.any(
            PurposeContent.service.has(Service.name.ilike(f"%{search}%"))
        ),
    )


def _handle_file_attachments(
    db: Session, db_purpose: Purpose, file_attachment_ids: list[int]
) -> None:
    """Handle file attachment updates for a purpose."""
    # Unlink files not in the new list
    current_file_ids = {f.id for f in db_purpose.file_attachments}
    new_file_ids = set(file_attachment_ids)
    files_to_unlink = current_file_ids - new_file_ids
    for file in files_to_unlink:
        file_service.delete_file(db, file)
    # Link new files
    file_service.link_files_to_purpose(db, file_attachment_ids, db_purpose.id)


def _process_emfs(db: Session, db_purpose: Purpose, emfs_data) -> None:
    """Process EMFs for purpose update."""
    existing_emfs = {emf.emf_id: emf for emf in db_purpose.emfs}
    updated_emfs = []

    # Loop through new patch EMFs
    for emf_data in emfs_data:
        emf_id = emf_data.emf_id

        if emf_id in existing_emfs:
            # Update existing EMF
            existing_emf = existing_emfs[emf_id]
            _update_existing_emf(db, existing_emf, emf_data)
            updated_emfs.append(existing_emf)
        else:
            # Create new EMF
            db_emf = _create_emf_with_costs(db, db_purpose.id, emf_data)
            updated_emfs.append(db_emf)

    # Set the updated EMFs list to the purpose
    db_purpose.emfs = updated_emfs


def get_purpose(db: Session, purpose_id: int) -> Purpose | None:
    """Get a single purpose by ID."""
    return _get_base_purpose_query(db).filter(Purpose.id == purpose_id).first()


def get_purposes(
    db: Session,
    pagination: PaginationParams,
    hierarchy_id: list[int] | None = None,
    supplier_id: list[int] | None = None,
    service_type_id: list[int] | None = None,
    service_id: list[int] | None = None,
    status: list[StatusEnum] | None = None,
    search: str | None = None,
    sort_by: str = "creation_time",
    sort_order: Literal["asc", "desc"] = "desc",
) -> tuple[list[Purpose], int]:
    """
    Get purposes with filtering, searching, sorting, and pagination.

    Returns:
        Tuple of (purposes list, total count)
    """
    query = _get_base_purpose_query(db)

    # Apply filters
    filters = []
    if hierarchy_id is not None and hierarchy_id:
        # Join with Hierarchy table to filter by path
        query = query.join(Hierarchy, Purpose.hierarchy_id == Hierarchy.id)
        hierarchy_filter = build_hierarchy_filter(db, hierarchy_id, Purpose)
        filters.append(hierarchy_filter)

    # Add basic filters
    basic_filters = _build_basic_filters(service_type_id, service_id, supplier_id, status)
    filters.extend(basic_filters)

    if filters:
        query = query.filter(and_(*filters))

    # Apply search
    if search:
        search_filter = _build_search_filter(search)
        query = query.filter(search_filter)

    # Apply sorting
    sort_column = getattr(Purpose, sort_by, Purpose.creation_time)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Apply pagination
    return paginate(query, pagination)


def create_purpose(db: Session, purpose: PurposeCreate) -> Purpose:
    """Create a new purpose with EMFs, contents, and link files."""
    # Validate unique services in purpose contents
    if purpose.contents:
        _validate_unique_services_in_purpose(purpose.contents)

    purpose_data = purpose.model_dump(
        exclude={"emfs", "file_attachment_ids", "contents"}
    )
    db_purpose = Purpose(**purpose_data)
    db.add(db_purpose)
    db.flush()

    # Create purpose contents if provided
    for content_data in purpose.contents:
        _create_purpose_content(db, db_purpose.id, content_data)

    # Create EMFs if provided
    for emf_data in purpose.emfs:
        _create_emf_with_costs(db, db_purpose.id, emf_data)

    # Link files to purpose if provided
    if purpose.file_attachment_ids:
        file_service.link_files_to_purpose(
            db, purpose.file_attachment_ids, db_purpose.id
        )

    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def patch_purpose(
    db: Session, purpose_id: int, purpose_update: PurposeUpdate
) -> Purpose | None:
    """Patch an existing purpose."""
    db_purpose = _get_base_purpose_query(db).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return None

    # Handle file attachments first
    if purpose_update.file_attachment_ids is not None:
        _handle_file_attachments(db, db_purpose, purpose_update.file_attachment_ids)

    # Update basic fields
    for field, value in purpose_update.model_dump(
        exclude_unset=True, exclude={"emfs", "file_attachment_ids", "contents"}
    ).items():
        setattr(db_purpose, field, value)

    # Handle EMFs separately
    if purpose_update.emfs is not None:
        _process_emfs(db, db_purpose, purpose_update.emfs)

    # Handle contents separately - replace all contents
    if purpose_update.contents is not None:
        # Validate unique services in purpose contents
        _validate_unique_services_in_purpose(purpose_update.contents)

        # Delete existing contents
        db.query(PurposeContent).filter(
            PurposeContent.purpose_id == db_purpose.id
        ).delete()

        # Create new contents
        for content_data in purpose_update.contents:
            _create_purpose_content(db, db_purpose.id, content_data)

    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def delete_purpose(db: Session, purpose_id: int) -> bool:
    """Delete a purpose and its associated files. Returns True if deleted, False if not found."""
    db_purpose = db.query(Purpose).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return False

    # Delete associated files from S3 and database
    for file in db_purpose.file_attachments:
        file_service.delete_file(db, file.id)

    db.delete(db_purpose)
    db.commit()
    return True
