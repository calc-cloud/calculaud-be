from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.pagination import PaginatedResult, PaginationParams, create_paginated_result
from app.predefined_flows import service
from app.predefined_flows.exceptions import (
    InvalidStageTypeId,
    PredefinedFlowAlreadyExists,
    PredefinedFlowNotFound,
)
from app.predefined_flows.schemas import (
    PredefinedFlowCreate,
    PredefinedFlowEditResponse,
    PredefinedFlowResponse,
    PredefinedFlowUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResult[PredefinedFlowResponse | PredefinedFlowEditResponse],
)
def get_predefined_flows(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search predefined flows by flow name (case-insensitive)"
    ),
    edit_format: bool = Query(
        False, description="Return flows in edit-friendly format with stage names"
    ),
    db: Session = Depends(get_db),
):
    """Get all predefined flows with pagination and optional search."""
    if edit_format:
        # Get flows and convert to edit format
        flows, total = service.get_predefined_flows(
            db=db, pagination=pagination, search=search
        )
        edit_flows = []
        for flow in flows:
            edit_flow = service.get_predefined_flow_edit_format(db, flow.id)
            if edit_flow:
                edit_flows.append(edit_flow)
        return create_paginated_result(edit_flows, total, pagination)
    else:
        flows, total = service.get_predefined_flows(
            db=db, pagination=pagination, search=search
        )
        return create_paginated_result(flows, total, pagination)


@router.get(
    "/{flow_id}", response_model=PredefinedFlowResponse | PredefinedFlowEditResponse
)
def get_predefined_flow(
    flow_id: int,
    edit_format: bool = Query(
        False, description="Return flow in edit-friendly format with stage names"
    ),
    db: Session = Depends(get_db),
):
    """Get a specific predefined flow by ID."""
    if edit_format:
        flow = service.get_predefined_flow_edit_format(db, flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Predefined flow not found",
            )
        return flow
    else:
        flow = service.get_predefined_flow(db, flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Predefined flow not found",
            )
        return flow


@router.post(
    "/",
    response_model=PredefinedFlowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_predefined_flow(
    flow: PredefinedFlowCreate,
    db: Session = Depends(get_db),
):
    """Create a new predefined flow."""
    try:
        return service.create_predefined_flow(db, flow)
    except PredefinedFlowAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except InvalidStageTypeId as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.patch(
    "/{flow_id}",
    response_model=PredefinedFlowResponse,
    dependencies=[Depends(require_admin)],
)
def patch_predefined_flow(
    flow_id: int,
    flow_update: PredefinedFlowUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing predefined flow."""
    try:
        return service.patch_predefined_flow(db, flow_id, flow_update)
    except PredefinedFlowNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except PredefinedFlowAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except InvalidStageTypeId as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete(
    "/{flow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_predefined_flow(
    flow_id: int,
    db: Session = Depends(get_db),
):
    """Delete a predefined flow."""
    try:
        service.delete_predefined_flow(db, flow_id)
    except PredefinedFlowNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
