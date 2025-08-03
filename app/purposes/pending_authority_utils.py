"""
Centralized pending authority logic for purposes.

Finds the responsible authority for the highest priority incomplete stage.
Both filters and model properties use these functions for consistency.
"""

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.purchases.models import Purchase
from app.responsible_authorities.models import ResponsibleAuthority
from app.stage_types.models import StageType
from app.stages.models import Stage


def _build_base_query(purpose_id, select_clause, purchase_id=None):
    """Build the base query for pending authority lookup."""
    return (
        select_clause.select_from(Purchase)
        .join(Stage, Purchase.id == Stage.purchase_id)
        .join(StageType, Stage.stage_type_id == StageType.id)
        .join(
            ResponsibleAuthority,
            StageType.responsible_authority_id == ResponsibleAuthority.id,
        )
        .where(
            Purchase.id == purchase_id if purchase_id else True,
            Purchase.purpose_id == purpose_id,
            StageType.responsible_authority_id.is_not(None),
        )
        .order_by(
            Stage.completion_date.is_(None).desc(),  # Incomplete stages first
            # For incomplete stages (completion_date IS NULL): use priority ASC (lowest number = highest priority)
            # For completed stages (completion_date IS NOT NULL): use priority DESC (highest number = lowest priority)
            case(
                (
                    Stage.completion_date.is_(None),
                    Stage.priority,
                ),  # Incomplete: priority value for ASC
                else_=-Stage.priority,  # Completed: negative priority for DESC effect
            ).asc(),
            StageType.id.asc(),
        )
        .limit(1)
    )


def get_pending_authority_id_query(purpose_id):
    """Get scalar subquery returning only the pending authority ID."""
    return _build_base_query(
        purpose_id, select(ResponsibleAuthority.id)
    ).scalar_subquery()


def get_pending_authority_object(
    db: Session, purpose_id: int, purchase_id: int | None = None
) -> ResponsibleAuthority | None:
    """Get the pending authority object for a purpose."""
    # Create a query that selects only the ResponsibleAuthority object
    query = _build_base_query(purpose_id, select(ResponsibleAuthority), purchase_id)
    return db.execute(query).scalar_one_or_none()
