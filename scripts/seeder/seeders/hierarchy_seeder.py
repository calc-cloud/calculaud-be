"""Seeder for hierarchical organizational structure."""

from typing import Any

from sqlalchemy.orm import Session

from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from scripts.seeder.config.settings import SeedingConfig
from scripts.seeder.core.base_seeder import BaseSeeder
from scripts.seeder.core.bulk_operations import BulkInserter
from scripts.seeder.utils.query_helpers import get_all_entities
from scripts.seeder.utils.sequence_sync import SequenceManager


class HierarchySeeder(BaseSeeder):
    """
    Seeder for organizational hierarchy structure.

    Seeds hierarchies from backup data with explicit IDs to maintain
    the organizational structure.
    """

    def seed(self, session: Session) -> dict[str, Any]:
        """
        Seed hierarchy data from backup.

        Args:
            session: Database session

        Returns:
            Dictionary with seeding statistics
        """
        results = {}

        # Check if hierarchies already exist
        existing_hierarchies = self._get_existing_hierarchy_ids(session)
        if existing_hierarchies:
            self.log(
                f"Found {len(existing_hierarchies)} existing hierarchies, using them..."
            )
            results["hierarchies"] = len(existing_hierarchies)
            return results

        self.log("🏢 Creating hierarchies from backup data...")

        with SequenceManager(session):
            hierarchy_ids = self._seed_hierarchies_from_backup(session)
            results["hierarchies"] = len(hierarchy_ids)

        self.log(f"   Created {len(hierarchy_ids)} hierarchies from backup")

        return results

    def _get_existing_hierarchy_ids(self, session: Session) -> list[int]:
        """
        Get existing hierarchy IDs from database.

        Args:
            session: Database session

        Returns:
            List of existing hierarchy IDs
        """
        hierarchies = get_all_entities(session, Hierarchy)
        return [h.id for h in hierarchies]

    def _seed_hierarchies_from_backup(self, session: Session) -> list[int]:
        """
        Create hierarchies from backup data.

        Args:
            session: Database session

        Returns:
            List of created hierarchy IDs
        """
        backup_data = SeedingConfig.get_hierarchy_backup_data()

        hierarchy_data_list = []
        hierarchy_ids = []

        for hierarchy_id, parent_id, type_str, name, path in backup_data:
            hierarchy_data = {
                "id": hierarchy_id,
                "parent_id": parent_id,
                "type": HierarchyTypeEnum(type_str),
                "name": name,
                "path": path,
            }
            hierarchy_data_list.append(hierarchy_data)
            hierarchy_ids.append(hierarchy_id)

        # Bulk insert hierarchies with explicit IDs
        bulk_inserter = BulkInserter(session)
        bulk_inserter.create_with_explicit_ids(Hierarchy, hierarchy_data_list)

        return hierarchy_ids
