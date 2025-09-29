"""Purchase API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.budget_sources.exceptions import BudgetSourceNotFound
from app.database import get_db
from app.purchases import service
from app.purchases.exceptions import PurchaseNotFound
from app.purchases.schemas import PurchaseCreate, PurchaseResponse, PurchaseUpdate
from app.stage_types.exceptions import StageTypeNotFound
from app.stages.exceptions import StageNotFound

router = APIRouter()


@router.post(
    "/",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_purchase(
    purchase_data: PurchaseCreate,
    db: Session = Depends(get_db),
):
    """Create a new purchase."""
    try:
        return service.create_purchase(db, purchase_data)
    except BudgetSourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
):
    """Get a purchase by ID."""
    try:
        return service.get_purchase(db, purchase_id)
    except PurchaseNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch(
    "/{purchase_id}",
    response_model=PurchaseResponse,
    dependencies=[Depends(require_admin)],
)
def patch_purchase(
    purchase_id: int,
    purchase_update: PurchaseUpdate,
    db: Session = Depends(get_db),
):
    """Patch an existing purchase."""
    try:
        return service.patch_purchase(db, purchase_id, purchase_update)
    except PurchaseNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except (BudgetSourceNotFound, StageNotFound, StageTypeNotFound) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete(
    "/{purchase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a purchase by ID."""
    try:
        service.delete_purchase(db, purchase_id)
    except PurchaseNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)
