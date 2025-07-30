"""Sorting utilities for purposes."""

from sqlalchemy import func, select

from app import Purchase, Stage


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
                func.case(
                    (
                        pending_stages.c.min_incomplete_priority > 1,
                        func.extract(
                            "day",
                            func.current_date()
                            - completed_stages.c.max_completion_date,
                        ),
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
