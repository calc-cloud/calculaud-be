from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    BudgetSourceCostDistributionResponse,
    BudgetSourceCostItem,
    ServiceTypeCostDistributionResponse,
    ServiceTypeCostItem, CurrencyAmounts,
)
from app.analytics.utils import calculate_multi_currency_totals
from app.budget_sources.models import BudgetSource
from app.costs.models import Cost, CurrencyEnum
from app.purchases.models import Purchase
from app.purposes.filters import apply_filters
from app.purposes.models import Purpose
from app.purposes.schemas import FilterParams
from app.service_types.models import ServiceType


class FinancialAnalyticsService:
    """Service for handling financial analytics calculations and data aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def get_cost_distribution_by_service_type(
        self, filters: FilterParams
    ) -> ServiceTypeCostDistributionResponse:
        """Get cost distribution by service type with multi-currency support.

        Returns cost totals for each service type in both USD and ILS currencies.
        Supports all universal filters and handles NULL service types as "Unknown".
        """
        # Query to get costs grouped by service type and currency
        query = (
            select(
                ServiceType.id.label("service_type_id"),
                ServiceType.name.label("service_type_name"),
                Cost.currency,
                func.sum(Cost.amount).label("total_amount"),
            )
            .select_from(Cost)
            .join(Purchase, Cost.purchase_id == Purchase.id)
            .join(Purpose, Purchase.purpose_id == Purpose.id)
            .outerjoin(ServiceType, Purpose.service_type_id == ServiceType.id)
        )

        # Apply universal filters
        query = apply_filters(query, filters, self.db)

        # Group by service type and currency
        query = query.group_by(
            ServiceType.id, ServiceType.name, Cost.currency
        ).order_by(ServiceType.name.nulls_last())

        result = self.db.execute(query).all()

        # Process results to aggregate by service type with multi-currency support
        service_type_data = {}

        for row in result:
            service_type_key = (
                row.service_type_id,
                row.service_type_name or "Unknown",
            )

            if service_type_key not in service_type_data:
                service_type_data[service_type_key] = {}

            service_type_data[service_type_key][row.currency] = float(row.total_amount)

        # Create final response with multi-currency calculations
        service_type_items = []
        for (
            service_type_id,
            service_type_name,
        ), currency_amounts in service_type_data.items():
            # Convert dictionary to schema
            currency_schema = CurrencyAmounts(
                ils=currency_amounts.get(CurrencyEnum.ILS, 0.0),
                support_usd=currency_amounts.get(CurrencyEnum.SUPPORT_USD, 0.0),
                available_usd=currency_amounts.get(CurrencyEnum.AVAILABLE_USD, 0.0),
            )
            amounts = calculate_multi_currency_totals(currency_schema)

            service_type_item = ServiceTypeCostItem(
                service_type_id=service_type_id,
                service_type_name=service_type_name,
                amounts=amounts,
            )
            service_type_items.append(service_type_item)

        # Sort by service type name for consistent ordering, with Unknown last
        service_type_items.sort(
            key=lambda x: (x.service_type_name == "Unknown", x.service_type_name)
        )

        return ServiceTypeCostDistributionResponse(data=service_type_items)

    def get_cost_distribution_by_budget_source(
        self, filters: FilterParams
    ) -> BudgetSourceCostDistributionResponse:
        """Get cost distribution by budget source with multi-currency support.

        Returns cost totals for each budget source in both USD and ILS currencies.
        Supports all universal filters and handles NULL budget sources as "Unknown".
        """
        # Query to get costs grouped by budget source and currency
        query = (
            select(
                BudgetSource.id.label("budget_source_id"),
                BudgetSource.name.label("budget_source_name"),
                Cost.currency,
                func.sum(Cost.amount).label("total_amount"),
            )
            .select_from(Cost)
            .join(Purchase, Cost.purchase_id == Purchase.id)
            .outerjoin(BudgetSource, Purchase.budget_source_id == BudgetSource.id)
            .join(Purpose, Purchase.purpose_id == Purpose.id)
        )

        # Apply universal filters
        query = apply_filters(query, filters, self.db)

        # Group by budget source and currency
        query = query.group_by(
            BudgetSource.id, BudgetSource.name, Cost.currency
        ).order_by(BudgetSource.name.nulls_last())

        result = self.db.execute(query).all()

        # Process results to aggregate by budget source with multi-currency support
        budget_source_data = {}

        for row in result:
            budget_source_key = (
                row.budget_source_id,
                row.budget_source_name or "Unknown",
            )

            if budget_source_key not in budget_source_data:
                budget_source_data[budget_source_key] = {}

            budget_source_data[budget_source_key][row.currency] = float(
                row.total_amount
            )

        # Create final response with multi-currency calculations
        budget_source_items = []
        for (
            budget_source_id,
            budget_source_name,
        ), currency_amounts in budget_source_data.items():
            # Convert dictionary to schema
            currency_schema = CurrencyAmounts(
                ils=currency_amounts.get(CurrencyEnum.ILS, 0.0),
                support_usd=currency_amounts.get(CurrencyEnum.SUPPORT_USD, 0.0),
                available_usd=currency_amounts.get(CurrencyEnum.AVAILABLE_USD, 0.0),
            )
            amounts = calculate_multi_currency_totals(currency_schema)

            budget_source_item = BudgetSourceCostItem(
                budget_source_id=budget_source_id,
                budget_source_name=budget_source_name,
                amounts=amounts,
            )
            budget_source_items.append(budget_source_item)

        # Sort by budget source name for consistent ordering, with Unknown last
        budget_source_items.sort(
            key=lambda x: (x.budget_source_name == "Unknown", x.budget_source_name)
        )

        return BudgetSourceCostDistributionResponse(data=budget_source_items)
