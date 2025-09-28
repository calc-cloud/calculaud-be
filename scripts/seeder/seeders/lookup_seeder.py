"""Seeder for lookup tables like ResponsibleAuthority and BudgetSource."""

from typing import Any

from sqlalchemy.orm import Session

from app.budget_sources.models import BudgetSource
from app.responsible_authorities.models import ResponsibleAuthority
from scripts.seeder.config.settings import SeedingConfig
from scripts.seeder.core.base_seeder import BaseSeeder
from scripts.seeder.core.bulk_operations import BulkInserter


class LookupSeeder(BaseSeeder):
    """Seeder for lookup tables that don't have complex relationships."""

    def seed(self, session: Session) -> dict[str, Any]:
        """
        Seed all lookup tables.

        Args:
            session: Database session

        Returns:
            Dictionary with seeding statistics
        """
        results = {}
        bulk_inserter = BulkInserter(session)

        # Seed responsible authorities
        if not self.should_skip(session, ResponsibleAuthority):
            self.log("🏛️ Creating responsible authorities...")
            authorities_data = SeedingConfig.get_responsible_authorities()
            authority_count = bulk_inserter.insert_from_data(
                ResponsibleAuthority, authorities_data
            )
            self.log(f"   Created {authority_count} responsible authorities")
            results["responsible_authorities"] = authority_count
        else:
            results["responsible_authorities"] = self.get_existing_count(
                session, ResponsibleAuthority
            )

        # Seed budget sources
        if not self.should_skip(session, BudgetSource):
            self.log("💰 Creating budget sources...")
            budget_sources_data = SeedingConfig.get_budget_sources()
            budget_source_count = bulk_inserter.insert_from_data(
                BudgetSource, budget_sources_data
            )
            self.log(f"   Created {budget_source_count} budget sources")
            results["budget_sources"] = budget_source_count
        else:
            results["budget_sources"] = self.get_existing_count(session, BudgetSource)

        return results
