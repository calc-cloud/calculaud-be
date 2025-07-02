from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.pagination import PaginationParams, paginate_select
from app.predefined_flows.exceptions import (
    InvalidStageTypeId,
    PredefinedFlowAlreadyExists,
    PredefinedFlowNotFound,
)
from app.predefined_flows.models import PredefinedFlow, PredefinedFlowStage
from app.predefined_flows.schemas import PredefinedFlowCreate, PredefinedFlowUpdate
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
    stmt = (
        select(PredefinedFlow)
        .options(
            joinedload(PredefinedFlow.predefined_flow_stages).joinedload(
                PredefinedFlowStage.stage_type
            )
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

    # Validate all stage type IDs exist
    all_stage_ids = []
    for stage_item in flow_data.stages:
        if isinstance(stage_item, list):
            all_stage_ids.extend(stage_item)
        else:
            all_stage_ids.append(stage_item)

    # Check each stage type exists
    for stage_type_id in all_stage_ids:
        stmt = select(StageType).where(StageType.id == stage_type_id)
        stage_type = db.execute(stmt).scalars().first()
        if not stage_type:
            raise InvalidStageTypeId(stage_type_id)

    # Create the predefined flow
    db_flow = PredefinedFlow(flow_name=flow_data.flow_name)
    db.add(db_flow)
    db.flush()  # Flush to get the ID

    # Create predefined flow stages with priorities
    _create_flow_stages(db, db_flow.id, flow_data.stages)

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
        # Validate all stage type IDs exist
        all_stage_ids = []
        for stage_item in update_data["stages"]:
            if isinstance(stage_item, list):
                all_stage_ids.extend(stage_item)
            else:
                all_stage_ids.append(stage_item)

        # Check each stage type exists
        for stage_type_id in all_stage_ids:
            stmt = select(StageType).where(StageType.id == stage_type_id)
            stage_type = db.execute(stmt).scalars().first()
            if not stage_type:
                raise InvalidStageTypeId(stage_type_id)

        # Delete existing stages
        for existing_stage in db_flow.predefined_flow_stages:
            db.delete(existing_stage)

        # Create new stages
        _create_flow_stages(db, db_flow.id, update_data["stages"])

    db.commit()
    db.refresh(db_flow)
    return db_flow


def _create_flow_stages(db: Session, flow_id: int, stages: list[int | list[int]]) -> None:
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