"""Seeder for base data like StageTypes and PredefinedFlows."""

from typing import Any

from sqlalchemy.orm import Session

from app.predefined_flows.models import PredefinedFlow, PredefinedFlowStage
from app.stage_types.models import StageType
from scripts.seeder.config.settings import SeedingConfig
from scripts.seeder.core.base_seeder import BaseSeeder
from scripts.seeder.core.bulk_operations import BulkInserter
from scripts.seeder.utils.query_helpers import get_entity_ids
from scripts.seeder.utils.sequence_sync import SequenceManager


class BaseDataSeeder(BaseSeeder):
    """
    Seeder for base data that's required for the system to function properly.

    This includes StageTypes and PredefinedFlows with their specific IDs
    from the backup data.
    """

    def seed(self, session: Session) -> dict[str, Any]:
        """
        Seed base data including stage types and predefined flows.

        Args:
            session: Database session

        Returns:
            Dictionary with seeding statistics
        """
        results = {}

        with SequenceManager(session):
            # Seed stage types first (required for predefined flows)
            stage_type_ids = self._seed_stage_types(session)
            results["stage_types"] = len(stage_type_ids)

            # Seed predefined flows
            flow_ids = self._seed_predefined_flows(session)
            results["predefined_flows"] = len(flow_ids)

        return results

    def _seed_stage_types(self, session: Session) -> list[int]:
        """
        Seed stage types from configuration data.

        Args:
            session: Database session

        Returns:
            List of created stage type IDs
        """
        if self.should_skip(session, StageType):
            return get_entity_ids(session, StageType)

        self.log("🎨 Creating stage types from configuration...")

        stage_flows_config = SeedingConfig.get_stage_flows()
        stage_types_data = stage_flows_config["stage_types"]

        bulk_inserter = BulkInserter(session)

        # Create stage types with explicit IDs
        stage_types = bulk_inserter.create_with_explicit_ids(
            StageType, stage_types_data
        )

        stage_type_ids = [st.id for st in stage_types]
        self.log(f"   Created {len(stage_type_ids)} stage types")

        return stage_type_ids

    def _seed_predefined_flows(self, session: Session) -> list[int]:
        """
        Seed predefined flows and their stages from configuration data.

        Args:
            session: Database session

        Returns:
            List of created predefined flow IDs
        """
        if self.should_skip(session, PredefinedFlow):
            return get_entity_ids(session, PredefinedFlow)

        self.log("= Creating predefined flows...")

        stage_flows_config = SeedingConfig.get_stage_flows()
        flows_config = stage_flows_config["predefined_flows"]

        bulk_inserter = BulkInserter(session)
        flow_ids = []

        for flow_name, flow_data in flows_config.items():
            # Create the predefined flow with explicit ID
            flow = PredefinedFlow(id=flow_data["id"], flow_name=flow_name)
            session.add(flow)
            session.flush()  # Need the flow ID for stages

            flow_ids.append(flow.id)

            # Create the predefined flow stages
            stage_data_list = []
            for stage_config in flow_data["stages"]:
                stage_data_list.append(
                    {
                        "predefined_flow_id": flow.id,
                        "stage_type_id": stage_config["stage_type_id"],
                        "priority": stage_config["priority"],
                    }
                )

            # Bulk insert the stages for this flow
            bulk_inserter.insert_from_data(PredefinedFlowStage, stage_data_list)

        self.log(f"   Created {len(flow_ids)} predefined flows")

        return flow_ids
