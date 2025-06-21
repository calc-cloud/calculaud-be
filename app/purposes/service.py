from typing import Literal

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.costs.models import Cost
from app.emfs.models import EMF
from app.files import service as file_service
from app.pagination import PaginationParams, paginate
from app.purposes.models import Purpose, StatusEnum
from app.purposes.schemas import PurposeCreate, PurposeUpdate


def get_purpose(db: Session, purpose_id: int) -> Purpose | None:
    """Get a single purpose by ID."""
    return (
        db.query(Purpose)
        .options(joinedload(Purpose.emfs), joinedload(Purpose.file_attachments))
        .filter(Purpose.id == purpose_id)
        .first()
    )


def get_purposes(
    db: Session,
    pagination: PaginationParams,
    hierarchy_id: int | None = None,
    supplier_id: int | None = None,
    service_type_id: int | None = None,
    status: StatusEnum | None = None,
    search: str | None = None,
    sort_by: str = "creation_time",
    sort_order: Literal["asc", "desc"] = "desc",
) -> tuple[list[Purpose], int]:
    """
    Get purposes with filtering, searching, sorting, and pagination.

    Returns:
        Tuple of (purposes list, total count)
    """
    query = db.query(Purpose).options(
        joinedload(Purpose.emfs), joinedload(Purpose.file_attachments)
    )

    # Apply filters
    filters = []
    if hierarchy_id is not None:
        filters.append(Purpose.hierarchy_id == hierarchy_id)

    if service_type_id is not None:
        filters.append(Purpose.service_type_id == service_type_id)

    if supplier_id is not None:
        filters.append(Purpose.supplier_id == supplier_id)

    if status:
        filters.append(Purpose.status == status)

    if filters:
        query = query.filter(and_(*filters))

    # Apply search
    if search:
        search_filter = or_(
            Purpose.description.ilike(f"%{search}%"),
            Purpose.content.ilike(f"%{search}%"),
        )
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
    """Create a new purpose with EMFs and link files."""
    purpose_data = purpose.model_dump(exclude={"emfs", "file_attachment_ids"})
    db_purpose = Purpose(**purpose_data)
    db.add(db_purpose)
    db.flush()

    # Create EMFs if provided
    for emf_data in purpose.emfs:
        emf_dict = emf_data.model_dump(exclude={"costs"})
        db_emf = EMF(**emf_dict, purpose_id=db_purpose.id)
        db.add(db_emf)
        db.flush()

        # Create costs for this EMF if provided
        for cost_data in emf_data.costs:
            db_cost = Cost(**cost_data.model_dump(), emf_id=db_emf.id)
            db.add(db_cost)

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
    db_purpose = db.query(Purpose).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return None

    # Handle file attachments first
    if purpose_update.file_attachment_ids is not None:
        # Unlink files not in the new list
        current_file_ids = {f.id for f in db_purpose.file_attachments}
        new_file_ids = set(purpose_update.file_attachment_ids)
        files_to_unlink = current_file_ids - new_file_ids
        for file in files_to_unlink:
            file_service.delete_file(db, file)
        # Link new files
        file_service.link_files_to_purpose(
            db, purpose_update.file_attachment_ids, db_purpose.id
        )

    # Update basic fields
    for field, value in purpose_update.model_dump(
        exclude_unset=True, exclude={"emfs", "file_attachment_ids"}
    ).items():
        setattr(db_purpose, field, value)

    # Handle EMFs separately
    if purpose_update.emfs is not None:
        existing_emfs = {emf.emf_id: emf for emf in db_purpose.emfs}
        updated_emfs = []

        # Loop through new patch EMFs
        for emf_data in purpose_update.emfs:
            emf_id = emf_data.emf_id

            if emf_id in existing_emfs:
                # Update existing EMF
                existing_emf = existing_emfs[emf_id]
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

                updated_emfs.append(existing_emf)
            else:
                # Create new EMF
                emf_dict = emf_data.model_dump(exclude={"costs"})
                db_emf = EMF(**emf_dict, purpose_id=db_purpose.id)
                db.add(db_emf)
                db.flush()

                # Create costs for new EMF if provided
                if emf_data.costs:
                    for cost_data in emf_data.costs:
                        db_cost = Cost(**cost_data.model_dump(), emf_id=db_emf.id)
                        db.add(db_cost)

                updated_emfs.append(db_emf)

        # Set the updated EMFs list to the purpose
        db_purpose.emfs = updated_emfs

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
