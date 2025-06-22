from typing import Literal

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.costs.models import Cost
from app.emfs.models import EMF
from app.hierarchies.models import Hierarchy
from app.pagination import PaginationParams, paginate
from app.purposes.models import Purpose, StatusEnum
from app.purposes.schemas import PurposeCreate, PurposeUpdate


def get_purpose(db: Session, purpose_id: int) -> Purpose | None:
    """Get a single purpose by ID."""
    return (
        db.query(Purpose)
        .options(joinedload(Purpose.emfs))
        .filter(Purpose.id == purpose_id)
        .first()
    )


def get_purposes(
    db: Session,
    pagination: PaginationParams,
    hierarchy_id: list[int] | None = None,
    supplier_id: list[int] | None = None,
    service_type_id: list[int] | None = None,
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
    query = db.query(Purpose).options(joinedload(Purpose.emfs))

    # Apply filters
    filters = []
    if hierarchy_id is not None and hierarchy_id:
        # Get the hierarchies to find their paths
        hierarchies = db.query(Hierarchy).filter(Hierarchy.id.in_(hierarchy_id)).all()
        if hierarchies:
            # Join with Hierarchy table to filter by path
            query = query.join(Hierarchy, Purpose.hierarchy_id == Hierarchy.id)
            # Find all purposes whose hierarchy path starts with any of the given hierarchy paths
            # This will include the hierarchies themselves and all their descendants
            hierarchy_filters = []
            for hierarchy in hierarchies:
                hierarchy_filters.append(Hierarchy.path.like(f"{hierarchy.path}%"))
            filters.append(or_(*hierarchy_filters))
        else:
            # If no hierarchies found, return empty result
            filters.append(Purpose.id == -1)  # This will never match

    if service_type_id is not None and service_type_id:
        filters.append(Purpose.service_type_id.in_(service_type_id))

    if supplier_id is not None and supplier_id:
        filters.append(Purpose.supplier_id.in_(supplier_id))

    if status is not None and status:
        filters.append(Purpose.status.in_(status))

    if filters:
        query = query.filter(and_(*filters))

    # Apply search
    if search:
        search_filter = or_(
            Purpose.description.ilike(f"%{search}%"),
            Purpose.content.ilike(f"%{search}%"),
            Purpose.emfs.any(EMF.emf_id.ilike(f"%{search}%")),
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
    """Create a new purpose with EMFs."""
    purpose_data = purpose.model_dump(exclude={"emfs"})
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
    # Update basic fields

    for field, value in purpose_update.model_dump(
        exclude_unset=True, exclude={"emfs"}
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
    """Delete a purpose. Returns True if deleted, False if not found."""
    db_purpose = db.query(Purpose).filter(Purpose.id == purpose_id).first()
    if not db_purpose:
        return False

    db.delete(db_purpose)
    db.commit()
    return True
