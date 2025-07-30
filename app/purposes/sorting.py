"""Sorting utilities for purposes."""

from sqlalchemy import Date, case, desc, func, select

from app import Purchase, Stage
from app.purposes.models import Purpose


def apply_sorting(stmt, sort_by: str, sort_order: str):
    """
    Apply sorting to the given statement based on sort_by and sort_order parameters.

    Args:
        stmt: SQLAlchemy Select statement
        sort_by: Field to sort by
        sort_order: "asc" or "desc"

    Returns:
        Modified Select statement with sorting applied
    """
    if sort_by == "days_since_last_completion":
        # Special handling for days_since_last_completion sorting
        days_subquery = build_days_since_last_completion_subquery()
        stmt = stmt.outerjoin(days_subquery, Purpose.id == days_subquery.c.purpose_id)

        if sort_order == "desc":
            sort_column = desc(days_subquery.c.days_since_last_completion).nulls_last()
        else:
            sort_column = days_subquery.c.days_since_last_completion.nulls_last()
    else:
        # Standard column sorting
        sort_column = getattr(Purpose, sort_by, Purpose.creation_time)

        if sort_order == "desc":
            sort_column = desc(sort_column)

    return stmt.order_by(sort_column)


def build_days_since_last_completion_subquery():
    """
    Build subquery to calculate max days_since_last_completion per purpose.

    Returns the maximum days since last completion across all purchases for each purpose,
    matching the logic from PurchaseResponse.days_since_last_completion.
    """
    # Subquery to find minimum incomplete priority per purchase
    pending_stages = (
        select(
            Stage.purchase_id, func.min(Stage.priority).label("min_incomplete_priority")
        )
        .where(Stage.completion_date.is_(None))
        .group_by(Stage.purchase_id)
        .subquery()
    )

    # Subquery to find max completion date per purchase/priority
    completed_stages = (
        select(
            Stage.purchase_id,
            Stage.priority,
            func.max(Stage.completion_date).label("max_completion_date"),
        )
        .where(Stage.completion_date.is_not(None))
        .group_by(Stage.purchase_id, Stage.priority)
        .subquery()
    )

    # Main subquery to calculate days since last completion
    days_subquery = (
        select(
            Purchase.purpose_id,
            func.max(
                case(
                    (
                        pending_stages.c.min_incomplete_priority > 1,
                        func.cast(func.current_date(), Date)
                        - func.cast(completed_stages.c.max_completion_date, Date),
                    ),
                    else_=None,
                )
            ).label("days_since_last_completion"),
        )
        .select_from(Purchase)
        .outerjoin(pending_stages, pending_stages.c.purchase_id == Purchase.id)
        .outerjoin(
            completed_stages,
            (completed_stages.c.purchase_id == Purchase.id)
            & (
                completed_stages.c.priority
                == pending_stages.c.min_incomplete_priority - 1
            ),
        )
        .group_by(Purchase.purpose_id)
        .subquery()
    )

    return days_subquery
