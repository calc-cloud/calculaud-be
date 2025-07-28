from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.pagination import PaginationParams, paginate_select
from app.predefined_flows.exceptions import (
    InvalidStageTypeId,
    PredefinedFlowAlreadyExists,
    PredefinedFlowNotFound,
)
from app.predefined_flows.models import PredefinedFlow, PredefinedFlowStage
from app.predefined_flows.schemas import (
    PredefinedFlowCreate,
    PredefinedFlowEditResponse,
    PredefinedFlowUpdate,
)
from app.stage_types.models import StageType


def get_predefined_flow(db: Session, flow_id: int) -> PredefinedFlow | None:
    """Get a single predefined flow by ID with eager loaded stages."""
    stmt = (
        select(PredefinedFlow)
        .options(
            joinedload(PredefinedFlow.predefined_flow_stages).joinedload(
                PredefinedFlowStage.stage_type
            )
        )
        .where(PredefinedFlow.id == flow_id)
    )
    return db.execute(stmt).scalars().first()


def resolve_stage_names_to_ids(
    db: Session, stages: list[int | str | list[int | str]]
) -> list[int | list[int]]:
    """Convert stage names to IDs in the stages structure."""
    resolved_stages = []

    for stage_item in stages:
        if isinstance(stage_item, list):
            # Handle list of stages (same priority)
            resolved_group = []
            for stage in stage_item:
                if isinstance(stage, str):
                    # Convert name to ID
                    stmt = select(StageType).where(StageType.name == stage)
                    stage_type = db.execute(stmt).scalars().first()
                    if not stage_type:
                        raise InvalidStageTypeId(stage)
                    resolved_group.append(stage_type.id)
                else:
                    # Already an ID, validate it exists
                    stmt = select(StageType).where(StageType.id == stage)
                    stage_type = db.execute(stmt).scalars().first()
                    if not stage_type:
                        raise InvalidStageTypeId(stage)
                    resolved_group.append(stage)
            resolved_stages.append(resolved_group)
        else:
            # Single stage
            if isinstance(stage_item, str):
                # Convert name to ID
                stmt = select(StageType).where(StageType.name == stage_item)
                stage_type = db.execute(stmt).scalars().first()
                if not stage_type:
                    raise InvalidStageTypeId(stage_item)
                resolved_stages.append(stage_type.id)
            else:
                # Already an ID, validate it exists
                stmt = select(StageType).where(StageType.id == stage_item)
                stage_type = db.execute(stmt).scalars().first()
                if not stage_type:
                    raise InvalidStageTypeId(stage_item)
                resolved_stages.append(stage_item)

    return resolved_stages


def get_predefined_flow_edit_format(
    db: Session, flow_id: int
) -> PredefinedFlowEditResponse | None:
    """Get predefined flow in edit-friendly format with stage names."""
    flow = get_predefined_flow(db, flow_id)
    if not flow:
        return None

    # Convert flow_stages to simple stage names array
    stages = []
    for stage_item in flow.flow_stages:
        if isinstance(stage_item, list):
            # Multiple stages with same priority
            stage_names = [stage.stage_type.name for stage in stage_item]
            stages.append(stage_names)
        else:
            # Single stage
            stages.append(stage_item.stage_type.name)

    return PredefinedFlowEditResponse(
        id=flow.id, flow_name=flow.flow_name, created_at=flow.created_at, stages=stages
    )


def get_predefined_flow_by_name(db: Session, flow_name: str) -> PredefinedFlow:
    """Get a single predefined flow by name with eager loaded stages."""
    stmt = (
        select(PredefinedFlow)
        .options(
            joinedload(PredefinedFlow.predefined_flow_stages).joinedload(
                PredefinedFlowStage.stage_type
            )
        )
        .where(PredefinedFlow.flow_name == flow_name)
    )
    flow = db.execute(stmt).scalars().first()
    if not flow:
        raise PredefinedFlowNotFound(flow_name)
    return flow


def get_predefined_flows(
    db: Session, pagination: PaginationParams, search: str | None = None
) -> tuple[list[PredefinedFlow], int]:
    """
    Get predefined flows with pagination and optional search.

    Args:
        db: Database session
        pagination: Pagination parameters
        search: Optional search term for flow name (case-insensitive)

    Returns:
        Tuple of (flows list, total count)
    """
    stmt = select(PredefinedFlow).options(
        joinedload(PredefinedFlow.predefined_flow_stages).joinedload(
            PredefinedFlowStage.stage_type
        )
    )

    # Apply search filter if provided
    if search:
        stmt = stmt.where(PredefinedFlow.flow_name.ilike(f"%{search}%"))

    # Apply ordering
    stmt = stmt.order_by(PredefinedFlow.flow_name)

    return paginate_select(db, stmt, pagination)


def create_predefined_flow(
    db: Session, flow_data: PredefinedFlowCreate
) -> PredefinedFlow:
    """Create a new predefined flow with stages."""
    # Check if flow with this name already exists
    stmt = select(PredefinedFlow).where(PredefinedFlow.flow_name == flow_data.flow_name)
    existing = db.execute(stmt).scalars().first()
    if existing:
        raise PredefinedFlowAlreadyExists(flow_data.flow_name)

    # Resolve stage names to IDs and validate they exist
    resolved_stages = resolve_stage_names_to_ids(db, flow_data.stages)

    # Create the predefined flow
    db_flow = PredefinedFlow(flow_name=flow_data.flow_name)
    db.add(db_flow)
    db.flush()  # Flush to get the ID

    # Create predefined flow stages with priorities
    _create_flow_stages(db, db_flow.id, resolved_stages)

    db.commit()
    db.refresh(db_flow)
    return db_flow


def patch_predefined_flow(
    db: Session, flow_id: int, flow_update: PredefinedFlowUpdate
) -> PredefinedFlow:
    """Patch an existing predefined flow."""
    stmt = (
        select(PredefinedFlow)
        .options(joinedload(PredefinedFlow.predefined_flow_stages))
        .where(PredefinedFlow.id == flow_id)
    )
    db_flow = db.execute(stmt).scalars().first()
    if not db_flow:
        raise PredefinedFlowNotFound(flow_id)

    update_data = flow_update.model_dump(exclude_unset=True)

    # Check for name conflicts if name is being updated
    if "flow_name" in update_data and update_data["flow_name"] is not None:
        stmt = (
            select(PredefinedFlow)
            .where(PredefinedFlow.flow_name == update_data["flow_name"])
            .where(PredefinedFlow.id != flow_id)
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            raise PredefinedFlowAlreadyExists(update_data["flow_name"])

    # Update flow name if provided
    if "flow_name" in update_data:
        db_flow.flow_name = update_data["flow_name"]

    # Update stages if provided
    if "stages" in update_data and update_data["stages"] is not None:
        # Resolve stage names to IDs and validate they exist
        resolved_stages = resolve_stage_names_to_ids(db, update_data["stages"])

        # Delete existing stages
        for existing_stage in db_flow.predefined_flow_stages:
            db.delete(existing_stage)

        # Create new stages
        _create_flow_stages(db, db_flow.id, resolved_stages)

    db.commit()
    db.refresh(db_flow)
    return db_flow


def _create_flow_stages(
    db: Session, flow_id: int, stages: list[int | list[int]]
) -> None:
    """Create predefined flow stages with priorities using enumerate."""
    for priority, stage_item in enumerate(stages, start=1):
        if isinstance(stage_item, list):
            # Multiple stages with same priority
            for stage_type_id in stage_item:
                db_stage = PredefinedFlowStage(
                    predefined_flow_id=flow_id,
                    stage_type_id=stage_type_id,
                    priority=priority,
                )
                db.add(db_stage)
        else:
            # Single stage
            db_stage = PredefinedFlowStage(
                predefined_flow_id=flow_id,
                stage_type_id=stage_item,
                priority=priority,
            )
            db.add(db_stage)


def delete_predefined_flow(db: Session, flow_id: int) -> None:
    """Delete a predefined flow."""
    stmt = select(PredefinedFlow).where(PredefinedFlow.id == flow_id)
    db_flow = db.execute(stmt).scalars().first()
    if not db_flow:
        raise PredefinedFlowNotFound(flow_id)

    db.delete(db_flow)
    db.commit()
