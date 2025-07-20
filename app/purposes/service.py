import csv
import io
from datetime import datetime
from typing import BinaryIO, Sequence

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, joinedload

from app import FileAttachment, Purchase, Stage
from app.files import service as file_service
from app.files.models import purpose_file_attachment
from app.pagination import paginate_select
from app.purposes.exceptions import (
    DuplicateServiceInPurpose,
    FileAttachmentsNotFound,
    FileNotAttachedToPurpose,
    PurposeNotFound,
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
from app.services.models import Service

# Stage type name constants
EMF_ID_STAGE_NAME = "emf_id"
BIKUSHIT_ID_STAGE_NAME = "bikushit_id"
DEMAND_ID_STAGE_NAME = "demand_id"
ORDER_ID_STAGE_NAME = "order_id"


def _get_base_purpose_select():
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


def _validate_unique_services_in_purpose(services: Sequence[PurposeContentBase]) -> None:
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


def _build_search_filter(search: str):
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
    stmt = _get_base_purpose_select().where(Purpose.id == purpose_id)
    return db.execute(stmt).unique().scalars().first()


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


def upload_file_to_purpose(
    db: Session, purpose_id: int, file_obj: BinaryIO, filename: str, content_type: str
):
    """Upload a file and attach it to a specific purpose."""
    # Check if purpose exists
    db_purpose = get_purpose(db, purpose_id)
    if not db_purpose:
        raise PurposeNotFound(purpose_id)

    # Upload file using existing file service
    file_response = file_service.upload_file(db, file_obj, filename, content_type)

    # Get the file attachment and add it to the purpose
    stmt = select(FileAttachment).where(FileAttachment.id == file_response.file_id)
    file_attachment = db.execute(stmt).scalar_one()

    # Add file to purpose's file_attachments
    db_purpose.file_attachments.append(file_attachment)
    db.commit()

    return file_response


def delete_file_from_purpose(db: Session, purpose_id: int, file_id: int) -> None:
    """Remove a file from a purpose and delete the file entirely."""
    # Check if purpose exists
    db_purpose = get_purpose(db, purpose_id)
    if not db_purpose:
        raise PurposeNotFound(purpose_id)

    stmt = select(purpose_file_attachment.c.file_attachment_id).where(
        purpose_file_attachment.c.purpose_id == purpose_id,
        purpose_file_attachment.c.file_attachment_id == file_id,
    )
    attachment_exists = db.execute(stmt).scalar_one_or_none()

    if not attachment_exists:
        raise FileNotAttachedToPurpose(file_id, purpose_id)

    # Get the file attachment to remove it from the purpose
    stmt = select(FileAttachment).where(FileAttachment.id == file_id)
    file_attachment = db.execute(stmt).scalar_one()

    # Remove file from purpose's file_attachments
    db_purpose.file_attachments.remove(file_attachment)

    # Delete the file entirely using existing file service
    file_service.delete_file(db, file_id)

    db.commit()


def export_purposes_csv(db: Session, params: GetPurposesRequest) -> str:
    """
    Export purposes as CSV with filtering, searching, and sorting.
    Returns all purposes without pagination.
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

    # Execute query without pagination to get all results
    purposes = db.execute(stmt).unique().scalars().all()

    # Convert to CSV with proper quoting for multi-line content
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    # Write header row
    header = [
        'ID',
        'Description',
        'Status',
        'Creation Time',
        'Last Modified',
        'Expected Delivery',
        'Comments',
        'Hierarchy',
        'Supplier',
        'Service Type',
        'Services',
        'Purchases',
        'EMF IDs',
        'EMF IDs Completion Date',
        'Bikushit IDs',
        'Bikushit IDs Completion Date',
        'Demand IDs',
        'Demand IDs Completion Date',
        'Order IDs',
        'Order IDs Completion Date',
        'Pending Stages',
        'File Attachments'
    ]
    writer.writerow(header)
    
    # Write data rows
    for purpose in purposes:
        # Aggregate services with quantity before service name
        services = '\n'.join([
            f"{content.quantity} {content.service_name}"
            for content in purpose.contents
        ])
        
        # Get purchase IDs (each on its own line)
        purchase_ids = [str(purchase.id) for purchase in purpose.purchases]
        purchase_ids_str = '\n'.join(purchase_ids)
        
        # Extract IDs and completion dates from purchases stages, maintaining purchase order and relationship
        emf_ids = []
        emf_completion_dates = []
        bikushit_ids = []
        bikushit_completion_dates = []
        demand_ids = []
        demand_completion_dates = []
        order_ids = []
        order_completion_dates = []
        
        # Process purchases in order to maintain relationships between IDs and completion dates
        for purchase in purpose.purchases:
            # Find IDs and completion dates for this specific purchase
            purchase_emf_id = ""
            purchase_emf_completion_date = ""
            purchase_bikushit_id = ""
            purchase_bikushit_completion_date = ""
            purchase_demand_id = ""
            purchase_demand_completion_date = ""
            purchase_order_id = ""
            purchase_order_completion_date = ""
            
            for stage in purchase.stages:
                if stage.stage_type.name == EMF_ID_STAGE_NAME and stage.value:
                    purchase_emf_id = stage.value
                    purchase_emf_completion_date = stage.completion_date.isoformat() if stage.completion_date else ""
                elif stage.stage_type.name == BIKUSHIT_ID_STAGE_NAME and stage.value:
                    purchase_bikushit_id = stage.value
                    purchase_bikushit_completion_date = stage.completion_date.isoformat() if stage.completion_date else ""
                elif stage.stage_type.name == DEMAND_ID_STAGE_NAME and stage.value:
                    purchase_demand_id = stage.value
                    purchase_demand_completion_date = stage.completion_date.isoformat() if stage.completion_date else ""
                elif stage.stage_type.name == ORDER_ID_STAGE_NAME and stage.value:
                    purchase_order_id = stage.value
                    purchase_order_completion_date = stage.completion_date.isoformat() if stage.completion_date else ""
            
            # Only add entries if at least one ID exists for this purchase
            if purchase_emf_id or purchase_bikushit_id or purchase_demand_id or purchase_order_id:
                emf_ids.append(purchase_emf_id)
                emf_completion_dates.append(purchase_emf_completion_date)
                bikushit_ids.append(purchase_bikushit_id)
                bikushit_completion_dates.append(purchase_bikushit_completion_date)
                demand_ids.append(purchase_demand_id)
                demand_completion_dates.append(purchase_demand_completion_date)
                order_ids.append(purchase_order_id)
                order_completion_dates.append(purchase_order_completion_date)
        
        # Join IDs and completion dates with newlines (each on its own line, maintaining purchase order)
        emf_ids_str = '\n'.join(emf_ids)
        emf_completion_dates_str = '\n'.join(emf_completion_dates)
        bikushit_ids_str = '\n'.join(bikushit_ids)
        bikushit_completion_dates_str = '\n'.join(bikushit_completion_dates)
        demand_ids_str = '\n'.join(demand_ids)
        demand_completion_dates_str = '\n'.join(demand_completion_dates)
        order_ids_str = '\n'.join(order_ids)
        order_completion_dates_str = '\n'.join(order_completion_dates)
        
        # Calculate pending stages for all purchases
        pending_stages_list = []
        for purchase in purpose.purchases:
            # Get current pending stages and days since last completion
            flow_stages = purchase.flow_stages
            if not flow_stages:
                pending_stages_list.append("")
                continue
            
            # Find the first priority level with incomplete stages
            current_pending_stages = []
            for stages in flow_stages:
                if isinstance(stages, list):
                    # Multiple stages at this priority, check if any is incomplete
                    incomplete_stages = [
                        stage for stage in stages if stage.completion_date is None
                    ]
                    if incomplete_stages:
                        current_pending_stages = incomplete_stages
                        break
                else:
                    # Single stage at this priority
                    if stages.completion_date is None:
                        current_pending_stages = [stages]
                        break
            
            if not current_pending_stages:
                pending_stages_list.append("")
                continue
            
            # Calculate days since last completion
            current_pending_priority = current_pending_stages[0].priority
            
            if current_pending_priority == 1:
                most_recent_completion_date = purchase.creation_date.date()
            else:
                # Get the previous completed stages
                last_completed_stages = flow_stages[current_pending_priority - 2]
                if isinstance(last_completed_stages, list):
                    most_recent_completion_date = max(
                        stage.completion_date for stage in last_completed_stages
                    )
                else:
                    most_recent_completion_date = last_completed_stages.completion_date
            
            days_since_last_completion = (datetime.now().date() - most_recent_completion_date).days
            
            # Format pending stages names
            pending_stage_names = [stage.stage_type.name for stage in current_pending_stages]
            pending_stages_text = f"{days_since_last_completion} days in {', '.join(pending_stage_names)}"
            pending_stages_list.append(pending_stages_text)
        
        # Join pending stages info with newlines
        pending_stages_str = '\n'.join(pending_stages_list)
        
        # Get file attachment names
        file_attachments = '\n'.join([
            file.original_filename for file in purpose.file_attachments
        ])
        
        row = [
            purpose.id,
            purpose.description or '',
            purpose.status.value if purpose.status else '',
            purpose.creation_time.isoformat() if purpose.creation_time else '',
            purpose.last_modified.isoformat() if purpose.last_modified else '',
            purpose.expected_delivery.isoformat() if purpose.expected_delivery else '',
            purpose.comments or '',
            purpose.hierarchy.path if purpose.hierarchy else '',
            purpose.supplier or '',
            purpose.service_type or '',
            services,
            purchase_ids_str,
            emf_ids_str,
            emf_completion_dates_str,
            bikushit_ids_str,
            bikushit_completion_dates_str,
            demand_ids_str,
            demand_completion_dates_str,
            order_ids_str,
            order_completion_dates_str,
            pending_stages_str,
            file_attachments
        ]
        writer.writerow(row)
    
    return output.getvalue()
