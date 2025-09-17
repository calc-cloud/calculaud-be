"""Processing time analytics service for stage and purpose timing analysis."""

from collections import defaultdict

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AnalyticsFilterParams,
    PurposeProcessingTimeByServiceType,
    PurposeProcessingTimeDistributionResponse,
    StageProcessingTimeByServiceType,
    StageProcessingTimeByStageType,
    StageProcessingTimeDistributionResponse,
)
from app.analytics.utils import apply_analytics_filters
from app.purchases.models import Purchase
from app.purposes.models import Purpose, PurposeStatusHistory, StatusEnum
from app.service_types.models import ServiceType
from app.stage_types.models import StageType
from app.stages.models import Stage


class ProcessingTimeAnalyticsService:
    """Service for processing time analytics including stage and purpose timing calculations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_date_diff_expression(self, end_date_col, start_date_col):
        """Calculate date difference in days."""
        if self.db.bind.dialect.name == "sqlite":
            return func.julianday(func.date(end_date_col)) - func.julianday(
                start_date_col
            )
        return func.date(end_date_col) - start_date_col

    def get_purpose_processing_time_distribution(
        self, params: AnalyticsFilterParams
    ) -> PurposeProcessingTimeDistributionResponse:
        """
        Get purpose processing time distribution by service type.

        Calculates processing time from first EMF ID stage creation to purpose completion.
        Filters by completion date range and groups results by service type.
        """
        # Subquery to get the earliest EMF ID stage creation date per purpose
        emf_start_subquery = (
            select(
                Stage.purchase_id,
                func.min(Stage.completion_date).label("emf_start_date"),
            )
            .select_from(Stage)
            .join(StageType, Stage.stage_type_id == StageType.id)
            .where(and_(StageType.name == "emf_id", Stage.completion_date.isnot(None)))
            .group_by(Stage.purchase_id)
        ).subquery()

        # Subquery to get the latest completion status change per purpose
        completion_subquery = (
            select(
                PurposeStatusHistory.purpose_id,
                func.max(PurposeStatusHistory.changed_at).label("completion_date"),
            )
            .select_from(PurposeStatusHistory)
            .where(PurposeStatusHistory.new_status == StatusEnum.COMPLETED)
            .group_by(PurposeStatusHistory.purpose_id)
        ).subquery()

        # Get database-specific date difference expression
        date_diff_expr = self._get_date_diff_expression(
            completion_subquery.c.completion_date, emf_start_subquery.c.emf_start_date
        )

        # Main query to calculate processing times
        query = (
            select(
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                func.count().label("count"),
                func.avg(date_diff_expr).label("avg_processing_days"),
                func.min(date_diff_expr).label("min_processing_days"),
                func.max(date_diff_expr).label("max_processing_days"),
            )
            .select_from(Purpose)
            .join(completion_subquery, Purpose.id == completion_subquery.c.purpose_id)
            .join(Purchase, Purpose.id == Purchase.purpose_id)
            .join(emf_start_subquery, Purchase.id == emf_start_subquery.c.purchase_id)
            .join(ServiceType, Purpose.service_type_id == ServiceType.id)
        )

        # Apply analytics filters using completion date
        query = apply_analytics_filters(
            query, params, date_column=completion_subquery.c.completion_date
        )

        # Group by service type and sort by average processing time descending
        query = query.group_by(ServiceType.id, ServiceType.name).order_by(
            func.avg(date_diff_expr).desc()
        )

        result = self.db.execute(query).all()

        # Build response
        service_type_items = []
        total_purposes = 0

        for row in result:
            service_type_item = PurposeProcessingTimeByServiceType(
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                count=row.count,
                average_processing_days=round(float(row.avg_processing_days or 0), 2),
                min_processing_days=int(row.min_processing_days or 0),
                max_processing_days=int(row.max_processing_days or 0),
            )
            service_type_items.append(service_type_item)
            total_purposes += row.count

        return PurposeProcessingTimeDistributionResponse(
            service_types=service_type_items,
            total_purposes=total_purposes,
        )

    def get_stage_processing_times_by_stage_type(
        self, filters: AnalyticsFilterParams
    ) -> StageProcessingTimeDistributionResponse:
        """
        Get stage processing times grouped by stage type with service type breakdown.

        Calculates processing time for each completed stage following the same logic
        as calculate_days_since_previous_stage, including complex priority handling.

        Returns:
            StageProcessingTimeDistributionResponse with stage type breakdown and overall averages
        """
        # Subquery to find the most recent completion date for each purchase/priority combination
        completed_stages_by_priority = (
            select(
                Stage.purchase_id,
                Stage.priority,
                func.max(Stage.completion_date).label("max_completion_date"),
            )
            .where(Stage.completion_date.is_not(None))
            .group_by(Stage.purchase_id, Stage.priority)
            .subquery()
        )

        # Get database-specific date difference expression
        date_diff_expr = self._get_date_diff_expression(
            Stage.completion_date, completed_stages_by_priority.c.max_completion_date
        )

        # Main aggregated query
        service_type_query = (
            select(
                Stage.stage_type_id,
                StageType.name.label("stage_type_name"),
                StageType.display_name.label("stage_type_display_name"),
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                func.count().label("count"),
                func.avg(date_diff_expr).label("avg_processing_days"),
                func.min(date_diff_expr).label("min_processing_days"),
                func.max(date_diff_expr).label("max_processing_days"),
            )
            .select_from(Stage)
            .join(StageType, StageType.id == Stage.stage_type_id)
            .join(Purchase, Purchase.id == Stage.purchase_id)
            .join(Purpose, Purpose.id == Purchase.purpose_id)
            .join(ServiceType, ServiceType.id == Purpose.service_type_id)
            .join(
                completed_stages_by_priority,
                and_(
                    completed_stages_by_priority.c.purchase_id == Stage.purchase_id,
                    completed_stages_by_priority.c.priority == Stage.priority - 1,
                ),
            )
            .where(
                and_(
                    Stage.completion_date.is_not(None),  # Only completed stages
                    Stage.priority > 1,  # Exclude priority 1 stages
                    date_diff_expr >= 0,  # No negative processing times
                )
            )
            .group_by(
                Stage.stage_type_id,
                StageType.name,
                StageType.display_name,
                ServiceType.id,
                ServiceType.name,
            )
            .order_by(Stage.stage_type_id, ServiceType.name)
        )

        # Apply analytics filters
        service_type_query = apply_analytics_filters(
            service_type_query, filters, date_column=Purpose.creation_time
        )

        # Execute service type breakdown query
        service_type_results = self.db.execute(service_type_query).fetchall()

        # Group results by stage type using defaultdict
        stage_types_data = defaultdict(list)
        for row in service_type_results:
            stage_key = (
                row.stage_type_id,
                row.stage_type_name,
                row.stage_type_display_name,
            )

            # Create service type item with SQL-calculated values
            service_type_item = StageProcessingTimeByServiceType(
                service_type_id=row.service_type_id,
                service_type_name=row.service_type_name,
                count=row.count,
                avg_processing_days=round(float(row.avg_processing_days or 0), 2),
                min_processing_days=int(row.min_processing_days or 0),
                max_processing_days=int(row.max_processing_days or 0),
            )
            stage_types_data[stage_key].append(service_type_item)

        # Calculate overall statistics per stage type using another SQL query
        overall_query = (
            select(
                Stage.stage_type_id,
                func.count().label("overall_count"),
                func.avg(date_diff_expr).label("overall_avg_processing_days"),
                func.min(date_diff_expr).label("overall_min_processing_days"),
                func.max(date_diff_expr).label("overall_max_processing_days"),
            )
            .select_from(Stage)
            .join(Purchase, Purchase.id == Stage.purchase_id)
            .join(Purpose, Purpose.id == Purchase.purpose_id)
            .join(
                completed_stages_by_priority,
                and_(
                    completed_stages_by_priority.c.purchase_id == Stage.purchase_id,
                    completed_stages_by_priority.c.priority == Stage.priority - 1,
                ),
            )
            .where(
                and_(
                    Stage.completion_date.is_not(None),
                    Stage.priority > 1,
                    date_diff_expr >= 0,
                )
            )
            .group_by(Stage.stage_type_id)
        )

        # Apply same filters to overall query
        overall_query = apply_analytics_filters(
            overall_query, filters, date_column=Purpose.creation_time
        )

        overall_results = self.db.execute(overall_query).fetchall()
        overall_stats = {row.stage_type_id: row for row in overall_results}

        # Build final response with SQL-calculated values
        stage_type_items = []
        for stage_key, service_types in stage_types_data.items():
            stage_type_id, stage_type_name, stage_type_display_name = stage_key
            overall = overall_stats.get(stage_type_id)

            stage_type_item = StageProcessingTimeByStageType(
                stage_type_id=stage_type_id,
                stage_type_name=stage_type_name,
                stage_type_display_name=stage_type_display_name,
                service_types=service_types,
                overall_count=overall.overall_count if overall else 0,
                overall_avg_processing_days=(
                    round(float(overall.overall_avg_processing_days or 0), 2)
                    if overall
                    else 0.0
                ),
                overall_min_processing_days=(
                    int(overall.overall_min_processing_days or 0) if overall else 0
                ),
                overall_max_processing_days=(
                    int(overall.overall_max_processing_days or 0) if overall else 0
                ),
            )
            stage_type_items.append(stage_type_item)

        # Sort by stage type ID
        stage_type_items.sort(key=lambda x: x.stage_type_id)

        return StageProcessingTimeDistributionResponse(data=stage_type_items)
