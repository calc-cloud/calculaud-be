"""Enhanced mock data seeder with new fields and improved performance."""

import random
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budget_sources.models import BudgetSource
from app.costs.models import Cost, CurrencyEnum
from app.hierarchies.models import Hierarchy
from app.predefined_flows.models import PredefinedFlow
from app.purchases.consts import PredefinedFlowName
from app.purchases.models import Purchase
from app.purposes.models import Purpose, PurposeContent
from app.service_types.models import ServiceType
from app.services.models import Service
from app.stage_types.models import StageType
from app.stages.models import Stage
from app.suppliers.models import Supplier
from scripts.seeder.config.settings import SeedingConfig
from scripts.seeder.core.base_seeder import BaseSeeder
from scripts.seeder.core.bulk_operations import BulkInserter
from scripts.seeder.utils.random_generators import (
    MockDataGenerator,
    create_random_datetime,
    create_random_stage_value_9_digits,
    get_random_boolean,
    get_weighted_choice,
)


class MockDataSeeder(BaseSeeder):
    """Enhanced mock data seeder with new fields and improved performance."""

    def __init__(self, num_purposes: int = None, **kwargs):
        """Initialize the mock data seeder."""
        super().__init__(**kwargs)
        self.num_purposes = num_purposes or SeedingConfig.DEFAULT_PURPOSE_COUNT
        self.mock_generator = MockDataGenerator()

    def seed(self, session: Session) -> dict[str, Any]:
        """Seed mock data including purposes, purchases, costs, and stages."""
        results = {}

        # Get required entity IDs from database
        entity_ids = self._get_entity_ids(session)
        if not self._validate_entity_ids(entity_ids):
            raise ValueError(
                "Required reference data not found. Run base data seeding first."
            )

        self.log(
            f"🎨 Creating {self.num_purposes} purposes with purchases and costs..."
        )

        # Seed purposes with related entities
        purpose_results = self._seed_purposes_with_purchases_and_costs(
            session, entity_ids
        )
        results.update(purpose_results)

        # Complete some stages with realistic data
        stage_results = self._complete_random_stages(session)
        results.update(stage_results)

        return results

    def _get_entity_ids(self, session: Session) -> dict[str, Any]:
        """Get all required entity IDs from the database."""
        self.log("🔍 Gathering entity IDs from database...")

        # Use SQLAlchemy v2 syntax for queries
        hierarchy_ids = list(session.execute(select(Hierarchy.id)).scalars())
        supplier_ids = list(session.execute(select(Supplier.id)).scalars())
        service_type_ids = list(session.execute(select(ServiceType.id)).scalars())
        budget_source_ids = list(session.execute(select(BudgetSource.id)).scalars())

        # Get services grouped by service type
        services_by_type_id = {}
        for service_type_id in service_type_ids:
            stmt = select(Service.id).where(Service.service_type_id == service_type_id)
            service_ids = list(session.execute(stmt).scalars())
            services_by_type_id[service_type_id] = service_ids

        return {
            "hierarchy_ids": hierarchy_ids,
            "supplier_ids": supplier_ids,
            "service_type_ids": service_type_ids,
            "services_by_type_id": services_by_type_id,
            "budget_source_ids": budget_source_ids,
        }

    def _validate_entity_ids(self, entity_ids: dict[str, Any]) -> bool:
        """Validate that required entities exist."""
        required = ["hierarchy_ids", "supplier_ids", "service_type_ids"]
        for entity_name in required:
            if not entity_ids.get(entity_name):
                self.log(f"⚠️ Missing required {entity_name}", "🚨")
                return False
        return True

    def _seed_purposes_with_purchases_and_costs(
        self, session: Session, entity_ids: dict[str, Any]
    ) -> dict[str, Any]:
        """Create purposes with purchases and costs in bulk."""
        bulk_inserter = BulkInserter(
            session, batch_size=SeedingConfig.DEFAULT_BATCH_SIZE
        )

        purposes = []
        all_purchases = []
        all_costs = []
        all_purpose_contents = []

        # Generate all purposes first
        for _ in range(self.num_purposes):
            purpose_data = self.mock_generator.generate_purpose_data(
                entity_ids["hierarchy_ids"],
                entity_ids["supplier_ids"],
                entity_ids["service_type_ids"],
            )
            purpose = Purpose(**purpose_data)
            purposes.append(purpose)

        # Bulk insert purposes
        purpose_count = bulk_inserter.insert_models(purposes)
        session.flush()  # Get purpose IDs

        # Create related entities for each purpose
        for purpose in purposes:
            # Add purpose contents (services)
            if purpose.service_type_id and entity_ids["services_by_type_id"]:
                available_services = entity_ids["services_by_type_id"].get(
                    purpose.service_type_id, []
                )
                if available_services:
                    num_services = random.randint(1, min(3, len(available_services)))
                    selected_services = random.sample(available_services, num_services)

                    for service_id in selected_services:
                        content = PurposeContent(
                            purpose_id=purpose.id,
                            service_id=service_id,
                            quantity=random.randint(1, 10),
                        )
                        all_purpose_contents.append(content)

            # Create 1-2 purchases per purpose
            num_purchases = random.randint(1, 2)
            for _ in range(num_purchases):
                purchase_data = {"purpose_id": purpose.id}

                # Optionally assign budget source
                if entity_ids["budget_source_ids"] and get_random_boolean(0.7):
                    purchase_data["budget_source_id"] = random.choice(
                        entity_ids["budget_source_ids"]
                    )

                purchase = Purchase(**purchase_data)
                all_purchases.append(purchase)

        # Bulk insert purchases and get IDs
        purchase_count = bulk_inserter.insert_models(all_purchases)
        session.flush()

        # Create costs and stages for purchases
        for purchase in all_purchases:
            cost_data_list = self.mock_generator.generate_cost_data(purchase.id)
            for cost_data in cost_data_list:
                all_costs.append(Cost(**cost_data))

            # Create stages based on costs
            self._create_stages_for_purchase(session, purchase, all_costs)

        # Flush stages to database before bulk inserting other entities
        session.flush()

        # Bulk insert remaining entities
        content_count = bulk_inserter.insert_models(all_purpose_contents)
        cost_count = bulk_inserter.insert_models(all_costs)

        return {
            "purposes": purpose_count,
            "purchases": purchase_count,
            "costs": cost_count,
            "purpose_contents": content_count,
        }

    def _create_stages_for_purchase(
        self, session: Session, purchase: Purchase, all_costs: list[Cost]
    ) -> None:
        """Create stages for a purchase based on its costs."""
        # Get costs for this purchase
        purchase_costs = [c for c in all_costs if c.purchase_id == purchase.id]

        # Determine predefined flow based on costs
        flow_name = self._get_predefined_flow_for_costs(purchase_costs)
        if not flow_name:
            return

        # Find and assign predefined flow
        stmt = select(PredefinedFlow).where(PredefinedFlow.flow_name == flow_name)
        predefined_flow = session.execute(stmt).scalar_one_or_none()

        if predefined_flow:
            purchase.predefined_flow_id = predefined_flow.id

            # Create stages based on predefined flow
            for predefined_stage in predefined_flow.predefined_flow_stages:
                stage = Stage(
                    stage_type_id=predefined_stage.stage_type_id,
                    priority=predefined_stage.priority,
                    purchase_id=purchase.id,
                )
                session.add(stage)

    def _get_predefined_flow_for_costs(self, costs: list[Cost]) -> str | None:
        """Determine predefined flow name based on costs."""
        if not costs:
            return None

        total_amount = sum(cost.amount for cost in costs)
        is_above_400k = total_amount >= 400_000

        if len(costs) > 1:
            return (
                PredefinedFlowName.MIXED_USD_ABOVE_400K_FLOW.value
                if is_above_400k
                else PredefinedFlowName.MIXED_USD_FLOW.value
            )

        cost = costs[0]

        if cost.currency == CurrencyEnum.SUPPORT_USD:
            return (
                PredefinedFlowName.SUPPORT_USD_ABOVE_400K_FLOW.value
                if is_above_400k
                else PredefinedFlowName.SUPPORT_USD_FLOW.value
            )
        elif cost.currency == CurrencyEnum.AVAILABLE_USD:
            return PredefinedFlowName.AVAILABLE_USD_FLOW.value

        return PredefinedFlowName.ILS_FLOW.value

    def _complete_random_stages(self, session: Session) -> dict[str, Any]:
        """Complete stages based on purpose status and realistic business logic."""
        self.log("🎭 Completing stages with realistic business logic...")

        stmt = select(Purpose)
        purposes = session.execute(stmt).scalars().all()

        if not purposes:
            return {"completed_stages": 0}

        completed_count = 0
        for purpose in purposes:
            # If purpose has a completed status, all stages must be completed
            if purpose.status.value in ["COMPLETED", "SIGNED", "PARTIALLY_SUPPLIED"]:
                completed_count += self._complete_all_stages_for_purpose(
                    session, purpose.id
                )
            else:
                # For IN_PROGRESS, complete stages randomly but in priority order
                stmt = select(Purchase).where(Purchase.purpose_id == purpose.id)
                purchases = session.execute(stmt).scalars().all()
                for purchase in purchases:
                    completed_count += self._complete_stages_for_purchase(
                        session, purchase.id
                    )

        return {"completed_stages": completed_count}

    def _complete_stages_for_purchase(self, session: Session, purchase_id: int) -> int:
        """Complete stages in priority order for a specific purchase."""
        # Get stages grouped by priority
        stmt = (
            select(Stage)
            .where(Stage.purchase_id == purchase_id)
            .order_by(Stage.priority)
        )
        stages = session.execute(stmt).scalars().all()

        if not stages:
            return 0

        # Group stages by priority level
        stages_by_priority = {}
        for stage in stages:
            if stage.priority not in stages_by_priority:
                stages_by_priority[stage.priority] = []
            stages_by_priority[stage.priority].append(stage)

        priority_levels = sorted(stages_by_priority.keys())
        total_priority_levels = len(priority_levels)

        # Better randomization: more varied completion patterns for IN_PROGRESS
        # 30% chance of 0 stages, then decreasing probability
        completion_weights = [3, 2, 2, 2, 2, 1, 1, 1, 1, 1]
        max_priorities_to_complete = min(
            len(completion_weights), total_priority_levels + 1
        )

        priorities_to_complete = get_weighted_choice(
            list(range(max_priorities_to_complete)),
            completion_weights[:max_priorities_to_complete],
        )

        if priorities_to_complete == 0:
            return 0

        # Complete stages priority by priority
        base_date = create_random_datetime(
            SeedingConfig.STAGE_COMPLETION_YEARS_AGO, 0.5
        )

        completed = 0
        for i, priority_level in enumerate(priority_levels[:priorities_to_complete]):
            priority_stages = stages_by_priority[priority_level]

            # For stages at the same priority, complete all or none (they're parallel)
            for stage in priority_stages:
                # Check if stage type requires value
                stage_type = session.get(StageType, stage.stage_type_id)
                if stage_type and stage_type.value_required:
                    stage.value = create_random_stage_value_9_digits()

                # Progressive completion dates between priority levels
                days_offset = i * random.randint(
                    5, 15
                )  # 5-15 days between priority levels
                hours_offset = random.randint(0, 23)
                stage.completion_date = (
                    base_date + timedelta(days=days_offset, hours=hours_offset)
                ).date()
                completed += 1

        return completed

    def _complete_all_stages_for_purpose(
        self, session: Session, purpose_id: int
    ) -> int:
        """Complete all stages for all purchases in a purpose."""
        # Get all purchases for this purpose
        stmt = select(Purchase).where(Purchase.purpose_id == purpose_id)
        purchases = session.execute(stmt).scalars().all()

        total_completed = 0
        for purchase in purchases:
            # Get all stages for this purchase, ordered by priority
            stmt = (
                select(Stage)
                .where(Stage.purchase_id == purchase.id)
                .order_by(Stage.priority)
            )
            stages = session.execute(stmt).scalars().all()

            if not stages:
                continue

            # Complete all stages with progressive dates
            base_date = create_random_datetime(
                SeedingConfig.STAGE_COMPLETION_YEARS_AGO, 0.5
            )

            for i, stage in enumerate(stages):
                if (
                    stage.completion_date is None
                ):  # Only complete if not already completed
                    # Check if stage type requires value
                    stage_type = session.get(StageType, stage.stage_type_id)
                    if stage_type and stage_type.value_required:
                        stage.value = create_random_stage_value_9_digits()

                    # Progressive completion dates
                    days_offset = i * random.randint(3, 14)
                    stage.completion_date = (
                        base_date + timedelta(days=days_offset)
                    ).date()
                    total_completed += 1

        return total_completed
