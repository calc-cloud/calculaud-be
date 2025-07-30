from typing import Sequence

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, joinedload

from app import FileAttachment, Purchase, Stage
from app.pagination import paginate_select
from app.purposes.exceptions import (
    DuplicateServiceInPurpose,
    FileAttachmentsNotFound,
    ServiceNotFound,
)
from app.purposes.filters import apply_filters
from app.purposes.models import Purpose, PurposeContent
from app.purposes.schemas import (
    GetPurposesRequest,
    PurposeContentBase,
    PurposeCreate,
    PurposeUpdate,
)
from app.purposes.sorting import build_days_since_last_completion_subquery
from app.services.models import Service


def get_base_purpose_select():
    """Get base purpose select statement with all necessary joins."""
    return select(Purpose).options(
        joinedload(Purpose.file_attachments),
        joinedload(Purpose.contents)
        .joinedload(PurposeContent.service)
        .joinedload(Service.service_type),
        joinedload(Purpose.purchases)
        .joinedload(Purchase.stages)
        .joinedload(Stage.stage_type),
        joinedload(Purpose.purchases).joinedload(Purchase.costs),
    )


def _validate_service_exists(db: Session, service_id: int) -> None:
    """Validate that a service exists, raise ServiceNotFound if not."""
    stmt = select(Service).where(Service.id == service_id)
    service = db.execute(stmt).scalars().first()
    if not service:
        raise ServiceNotFound(service_id)


def _validate_unique_services_in_purpose(
    services: Sequence[PurposeContentBase],
) -> None:
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


def build_search_filter(search: str):
    """Build search filter for purpose queries."""
    return or_(
        Purpose.description.ilike(f"%{search}%"),
        Purpose.purchases.any(Purchase.stages.any(Stage.value.ilike(f"%{search}%"))),
        Purpose.contents.any(
            PurposeContent.service.has(Service.name.ilike(f"%{search}%"))
        ),
    )


def _set_file_attachments(
    db: Session, db_purpose: Purpose, file_attachment_ids: list[int]
) -> None:
    """Handle file attachment updates for a purpose using many-to-many relationship."""
    files = (
        db.execute(
            select(FileAttachment).where(FileAttachment.id.in_(file_attachment_ids))
        )
        .scalars()
        .all()
    )
    found_ids = {file.id for file in files}
    missing_ids = set(file_attachment_ids) - found_ids
    if missing_ids:
        raise FileAttachmentsNotFound(list(missing_ids))
    db_purpose.file_attachments = list(files)


def get_purpose(db: Session, purpose_id: int) -> Purpose | None:
    """Get a single purpose by ID."""
    stmt = get_base_purpose_select().where(Purpose.id == purpose_id)
    return db.execute(stmt).unique().scalars().first()


def get_purposes(db: Session, params: GetPurposesRequest) -> tuple[list[Purpose], int]:
    """
    Get purposes with filtering, searching, sorting, and pagination.

    Returns:
        Tuple of (purposes list, total count)
    """
    stmt = get_base_purpose_select()

    # Apply universal filters using the centralized filtering method
    stmt = apply_filters(stmt, params, db)

    # Apply search
    if params.search:
        search_filter = build_search_filter(params.search)
        stmt = stmt.where(search_filter)

    # Apply sorting
    if params.sort_by == "days_since_last_completion":
        # Special handling for days_since_last_completion sorting
        days_subquery = build_days_since_last_completion_subquery()
        stmt = stmt.outerjoin(days_subquery, Purpose.id == days_subquery.c.purpose_id)

        if params.sort_order == "desc":
            stmt = stmt.order_by(
                desc(days_subquery.c.days_since_last_completion.nulls_last())
            )
        else:
            stmt = stmt.order_by(
                days_subquery.c.days_since_last_completion.nulls_last()
            )
    else:
        # Standard column sorting
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

    purpose_data = purpose.model_dump(exclude={"file_attachment_ids", "contents"})
    db_purpose = Purpose(**purpose_data)
    db.add(db_purpose)
    db.flush()

    # Create purpose contents if provided
    for content_data in purpose.contents:
        _create_purpose_content(db, db_purpose.id, content_data)

    if purpose.file_attachment_ids:
        _set_file_attachments(db, db_purpose, purpose.file_attachment_ids)

    db.commit()
    db.refresh(db_purpose)
    return db_purpose


def patch_purpose(
    db: Session, purpose_id: int, purpose_update: PurposeUpdate
) -> Purpose | None:
    """Patch an existing purpose."""
    db_purpose = get_purpose(db, purpose_id)
    if not db_purpose:
        return None

    # Handle file attachments first
    if purpose_update.file_attachment_ids is not None:
        _set_file_attachments(db, db_purpose, purpose_update.file_attachment_ids)

    # Update basic fields
    for field, value in purpose_update.model_dump(
        exclude_unset=True, exclude={"file_attachment_ids", "contents"}
    ).items():
        setattr(db_purpose, field, value)

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
    """Delete a purpose. Returns True if deleted, False if not found."""
    stmt = select(Purpose).where(Purpose.id == purpose_id)
    db_purpose = db.execute(stmt).scalars().first()
    if not db_purpose:
        return False

    # With many-to-many relationship, files are automatically unlinked by cascade delete
    # Files themselves are not deleted since they might be linked to other purposes
    db.delete(db_purpose)
    db.commit()
    return True
