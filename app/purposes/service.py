from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, joinedload

from app.costs.models import Cost
from app.emfs.models import EMF
from app.files import service as file_service
from app.pagination import paginate_select
from app.purposes.exceptions import DuplicateServiceInPurpose, ServiceNotFound
from app.purposes.filters import apply_filters
from app.purposes.models import Purpose, PurposeContent
from app.purposes.schemas import (
    GetPurposesRequest,
    PurposeContentBase,
    PurposeCreate,
    PurposeUpdate,
)
from app.services.models import Service


def _get_base_purpose_select():
    """Get base purpose select statement with all necessary joins."""
    return select(Purpose).options(
        joinedload(Purpose.emfs),
        joinedload(Purpose.file_attachments),
        joinedload(Purpose.contents)
        .joinedload(PurposeContent.service)
        .joinedload(Service.service_type),
    )


def _validate_service_exists(db: Session, service_id: int) -> None:
    """Validate that a service exists, raise ServiceNotFound if not."""
    stmt = select(Service).where(Service.id == service_id)
    service = db.execute(stmt).scalars().first()
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
        stmt = select(Cost).where(Cost.emf_id == existing_emf.id)
        costs_to_delete = db.execute(stmt).scalars().all()
        for cost in costs_to_delete:
            db.delete(cost)
        for cost_data in emf_data.costs:
            db_cost = Cost(**cost_data.model_dump(), emf_id=existing_emf.id)
            db.add(db_cost)


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
    stmt = _get_base_purpose_select().where(Purpose.id == purpose_id)
    return db.execute(stmt).scalars().first()


def get_purposes(db: Session, params: GetPurposesRequest) -> tuple[list[Purpose], int]:
    """
    Get purposes with filtering, searching, sorting, and pagination.

    Returns:
        Tuple of (purposes list, total count)
    """
    stmt = _get_base_purpose_select()

    # Apply universal filters using the centralized filtering method
    stmt = apply_filters(stmt, params, db)

    # Apply search
    if params.search:
        search_filter = _build_search_filter(params.search)
        stmt = stmt.where(search_filter)

    # Apply sorting
    sort_column = getattr(Purpose, params.sort_by, Purpose.creation_time)
    if params.sort_order == "desc":
        stmt = stmt.order_by(desc(sort_column))
    else:
        stmt = stmt.order_by(sort_column)

    # Apply pagination
    return paginate_select(db, stmt, params)


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
    stmt = _get_base_purpose_select().where(Purpose.id == purpose_id)
    db_purpose = db.execute(stmt).scalars().first()
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
        stmt = select(PurposeContent).where(PurposeContent.purpose_id == db_purpose.id)
        contents_to_delete = db.execute(stmt).scalars().all()
        for content in contents_to_delete:
            db.delete(content)
        db.flush()  # Ensure deletions are committed before creating new ones

        # Create new contents
        for content_data in purpose_update.contents:
            _create_purpose_content(db, db_purpose.id, content_data)

    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def delete_purpose(db: Session, purpose_id: int) -> bool:
    """Delete a purpose and its associated files. Returns True if deleted, False if not found."""
    stmt = select(Purpose).where(Purpose.id == purpose_id)
    db_purpose = db.execute(stmt).scalars().first()
    if not db_purpose:
        return False

    # Delete associated files from S3 and database
    for file in db_purpose.file_attachments:
        file_service.delete_file(db, file.id)

    db.delete(db_purpose)
    db.commit()
    return True
