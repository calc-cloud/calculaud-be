"""Seeder for catalog data like service types, services, and suppliers."""

from typing import Any

from sqlalchemy.orm import Session

from app.service_types.models import ServiceType
from app.services.models import Service
from app.suppliers.models import Supplier
from scripts.seeder.config.settings import SeedingConfig
from scripts.seeder.core.base_seeder import BaseSeeder
from scripts.seeder.core.bulk_operations import BulkInserter
from scripts.seeder.utils.query_helpers import (
    get_all_entities,
    get_entities_by_attribute,
    get_entity_by_attribute,
    get_entity_ids,
)


class CatalogSeeder(BaseSeeder):
    """
    Seeder for catalog data including service types, services, and suppliers.

    This creates the reference data needed for purposes and purchases.
    """

    def seed(self, session: Session) -> dict[str, Any]:
        """
        Seed catalog data.

        Args:
            session: Database session

        Returns:
            Dictionary with seeding statistics and entity IDs
        """
        results = {}

        # Seed suppliers
        supplier_ids = self._seed_suppliers(session)
        results["suppliers"] = len(supplier_ids)
        results["supplier_ids"] = supplier_ids

        # Seed service types and services
        service_type_ids, services_by_type_id = self._seed_service_types_and_services(
            session
        )
        results["service_types"] = len(service_type_ids)
        results["service_type_ids"] = service_type_ids
        results["services_by_type_id"] = services_by_type_id

        # Count total services
        total_services = sum(len(services) for services in services_by_type_id.values())
        results["services"] = total_services

        return results

    def _seed_suppliers(self, session: Session) -> list[int]:
        """
        Seed supplier data from configuration.

        Args:
            session: Database session

        Returns:
            List of created supplier IDs
        """
        if self.should_skip(session, Supplier):
            return get_entity_ids(session, Supplier)

        self.log("📦 Creating suppliers...")

        suppliers_list = SeedingConfig.get_suppliers()

        # Convert supplier names to data dictionaries
        supplier_data_list = [{"name": name} for name in suppliers_list]

        bulk_inserter = BulkInserter(session)
        bulk_inserter.insert_from_data(Supplier, supplier_data_list)

        # Get the created supplier IDs
        supplier_ids = get_entity_ids(session, Supplier)

        self.log(f"   Created {len(supplier_ids)} suppliers")

        return supplier_ids

    def _seed_service_types_and_services(
        self, session: Session
    ) -> tuple[list[int], dict[int, list[int]]]:
        """
        Seed service types and their associated services.

        Args:
            session: Database session

        Returns:
            Tuple of (service_type_ids, services_by_type_id mapping)
        """
        service_type_ids = []
        services_by_type_id = {}

        # Skip if service types already exist
        if self.should_skip(session, ServiceType):
            service_types = get_all_entities(session, ServiceType)
            service_type_ids = [st.id for st in service_types]

            # Build services mapping for existing data
            for service_type in service_types:
                service_ids = [s.id for s in service_type.services]
                services_by_type_id[service_type.id] = service_ids

            return service_type_ids, services_by_type_id

        self.log("🔧 Creating service types and services...")

        service_types_config = SeedingConfig.get_service_types()
        bulk_inserter = BulkInserter(session)

        for service_type_name, service_names in service_types_config.items():
            # Create service type
            service_type_data = {"name": service_type_name}
            bulk_inserter.insert_from_data(ServiceType, [service_type_data])

            # Commit the transaction to ensure the service type is available
            session.commit()

            # Get the created service type
            service_type = get_entity_by_attribute(
                session, ServiceType, "name", service_type_name
            )

            if service_type is None:
                raise ValueError(f"Failed to create service type: {service_type_name}")

            service_type_ids.append(service_type.id)

            # Create services for this service type
            service_data_list = []
            for service_name in service_names:
                service_data_list.append(
                    {"name": service_name, "service_type_id": service_type.id}
                )

            bulk_inserter.insert_from_data(Service, service_data_list)

            # Get the created service IDs
            services = get_entities_by_attribute(
                session, Service, "service_type_id", service_type.id
            )
            service_ids = [s.id for s in services]
            services_by_type_id[service_type.id] = service_ids

        self.log(f"   Created {len(service_type_ids)} service types")

        # Count total services
        total_services = sum(len(services) for services in services_by_type_id.values())
        self.log(f"   Created {total_services} services")

        return service_type_ids, services_by_type_id
