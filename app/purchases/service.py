"""Service layer for purchase operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app import Stage, CurrencyEnum
from app.predefined_flows import service as predefined_flow_service
from app.purchases.exceptions import PurchaseNotFound
from app.purchases.models import Purchase
from app.purchases.consts import PredefinedFlowName
from app.purchases.schemas import PurchaseCreate


def create_purchase(db: Session, purchase_data: PurchaseCreate) -> Purchase:
    """Create a new purchase."""
    db_purchase = Purchase(**purchase_data.model_dump())
    db.add(db_purchase)

    # Get and store the predefined flow
    flow_name_enum = get_predefined_flow_for_purchase(db_purchase)
    if flow_name_enum is not None:
        predefined_flow = predefined_flow_service.get_predefined_flow_by_name(
            db, flow_name_enum.value
        )
        db_purchase.predefined_flow_id = predefined_flow.id

        # Create stages based on predefined flow
        stages = [
            Stage(
                stage_type_id=predefined_stage.stage_type_id,
                priority=predefined_stage.priority,
                purchase_id=db_purchase.id,
            ) for predefined_stage in predefined_flow.predefined_flow_stages
        ]
        db.add_all(stages)

    db.commit()
    db.refresh(db_purchase)

    return db_purchase


def get_purchase(db: Session, purchase_id: int) -> Purchase:
    """Get a purchase by ID with eager loaded stages and stage types."""
    stmt = (
        select(Purchase)
        .options(
            joinedload(Purchase.stages).joinedload(Stage.stage_type),
            joinedload(Purchase.predefined_flow),
            joinedload(Purchase.costs)
        )
        .where(Purchase.id == purchase_id)
    )
    purchase = db.execute(stmt).unique().scalar_one_or_none()

    if not purchase:
        raise PurchaseNotFound(purchase_id)

    return purchase


def delete_purchase(db: Session, purchase_id: int) -> None:
    """Delete a purchase by ID."""
    purchase = get_purchase(db, purchase_id)
    db.delete(purchase)
    db.commit()


def get_predefined_flow_for_purchase(purchase: Purchase) -> PredefinedFlowName | None:
    """Return predefined flow based on purchase attributes (fake logic for now)."""

    if not purchase.costs:
        return None

    is_amount_above_100k = sum(cost.amount for cost in purchase.costs) > 100_000

    if len(purchase.costs) > 1:
        if is_amount_above_100k:
            return PredefinedFlowName.MIXED_USD_ABOVE_100K
        else:
            return PredefinedFlowName.MIXED_USD_FLOW

    cost = purchase.costs[0]

    if cost.currency == CurrencyEnum.SUPPORT_USD:
        if is_amount_above_100k:
            return PredefinedFlowName.SUPPORT_USD_ABOVE_100K
        return PredefinedFlowName.SUPPORT_USD_FLOW

    elif cost.currency == CurrencyEnum.AVAILABLE_USD:
        return PredefinedFlowName.AVAILABLE_USD_FLOW

    return PredefinedFlowName.ILS_FLOW