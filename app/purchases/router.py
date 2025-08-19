"""Purchase API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.purchases import service
from app.purchases.exceptions import PurchaseNotFound
from app.purchases.schemas import PurchaseCreate, PurchaseResponse

router = APIRouter()


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    purchase_data: PurchaseCreate,
    db: Session = Depends(get_db),
):
    """Create a new purchase."""
    return service.create_purchase(db, purchase_data)


@router.get(
    "/{purchase_id}", response_model=PurchaseResponse, operation_id="get_purchase"
)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
):
    """Get a purchase by ID."""
    try:
        return service.get_purchase(db, purchase_id)
    except PurchaseNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a purchase by ID."""
    try:
        service.delete_purchase(db, purchase_id)
    except PurchaseNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)
