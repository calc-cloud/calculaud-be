from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.costs.models import Cost, CurrencyEnum
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.purchases.models import Purchase
from app.purposes.models import Purpose, PurposeContent, StatusEnum
from app.service_types.models import ServiceType
from app.services.models import Service
from app.suppliers.models import Supplier


class TestAnalyticsAPI:
    """Test suite for analytics API endpoints."""

    @pytest.fixture
    def setup_test_data(self, db_session: Session):
        """Set up test data for analytics tests."""

        # Create hierarchies
        unit = Hierarchy(type=HierarchyTypeEnum.UNIT, name="Test Unit")
        db_session.add(unit)
        db_session.flush()

        center = Hierarchy(
            type=HierarchyTypeEnum.CENTER, name="Test Center", parent_id=unit.id
        )
        db_session.add(center)
        db_session.flush()

        # Create service types
        service_type1 = ServiceType(name="Consulting")
        service_type2 = ServiceType(name="Equipment")
        db_session.add_all([service_type1, service_type2])
        db_session.flush()

        # Create services
        service1 = Service(name="IT Consulting", service_type_id=service_type1.id)
        service2 = Service(name="Software License", service_type_id=service_type1.id)
        service3 = Service(name="Hardware", service_type_id=service_type2.id)
        db_session.add_all([service1, service2, service3])
        db_session.flush()

        # Create supplier
        supplier = Supplier(name="Test Supplier")
        db_session.add(supplier)
        db_session.flush()

        # Create purposes
        purpose1 = Purpose(
            description="Purpose 1",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=center.id,
            service_type_id=service_type1.id,
            supplier_id=supplier.id,
            creation_time=datetime(2024, 1, 15),
        )
        purpose2 = Purpose(
            description="Purpose 2",
            status=StatusEnum.COMPLETED,
            hierarchy_id=center.id,
            service_type_id=service_type2.id,
            supplier_id=supplier.id,
            creation_time=datetime(2024, 2, 15),
        )
        db_session.add_all([purpose1, purpose2])
        db_session.flush()

        # Create purpose contents
        content1 = PurposeContent(
            purpose_id=purpose1.id, service_id=service1.id, quantity=5
        )
        content2 = PurposeContent(
            purpose_id=purpose1.id, service_id=service2.id, quantity=3
        )
        content3 = PurposeContent(
            purpose_id=purpose2.id, service_id=service3.id, quantity=2
        )
        db_session.add_all([content1, content2, content3])
        db_session.flush()

        # Create purchases
        purchase1 = Purchase(purpose_id=purpose1.id)
        purchase2 = Purchase(purpose_id=purpose2.id)
        db_session.add_all([purchase1, purchase2])
        db_session.flush()

        # Create costs
        cost1 = Cost(purchase_id=purchase1.id, currency=CurrencyEnum.ILS, amount=1000.0)
        cost2 = Cost(
            purchase_id=purchase1.id, currency=CurrencyEnum.SUPPORT_USD, amount=200.0
        )
        cost3 = Cost(purchase_id=purchase2.id, currency=CurrencyEnum.ILS, amount=1500.0)
        db_session.add_all([cost1, cost2, cost3])

        db_session.commit()

        return {
            "unit": unit,
            "center": center,
            "service_type1": service_type1,
            "service_type2": service_type2,
            "service1": service1,
            "service2": service2,
            "service3": service3,
            "supplier": supplier,
            "purpose1": purpose1,
            "purpose2": purpose2,
        }

    def test_get_services_quantities(self, test_client: TestClient, setup_test_data):
        """Test services quantities endpoint with stacked format."""

        response = test_client.get("/api/v1/analytics/services/quantities")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        # Should have 2 service types: Consulting and Equipment
        assert len(data["data"]) == 2

        # Check service type structure
        service_type_names = [item["service_type_name"] for item in data["data"]]
        assert "Consulting" in service_type_names
        assert "Equipment" in service_type_names

        # Check structure of service type items
        consulting_item = next(
            item for item in data["data"] if item["service_type_name"] == "Consulting"
        )
        assert "service_type_id" in consulting_item
        assert "service_type_name" in consulting_item
        assert "total_quantity" in consulting_item
        assert "services" in consulting_item

        # Check services breakdown
        assert len(consulting_item["services"]) == 2
        assert consulting_item["total_quantity"] == 8  # 5 + 3

        # Check individual services in breakdown
        service_names = [
            service["service_name"] for service in consulting_item["services"]
        ]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names

        # Check service structure
        first_service = consulting_item["services"][0]
        assert "service_id" in first_service
        assert "service_name" in first_service
        assert "quantity" in first_service

    def test_get_services_quantities_with_filters(
        self, test_client: TestClient, setup_test_data
    ):
        """Test services quantities with date filters."""

        response = test_client.get(
            "/api/v1/analytics/services/quantities",
            params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include service types from January (purpose1 - only Consulting type)
        assert len(data["data"]) == 1
        service_type_names = [item["service_type_name"] for item in data["data"]]
        assert "Consulting" in service_type_names

        # Check that it includes the correct services
        consulting_item = data["data"][0]
        service_names = [
            service["service_name"] for service in consulting_item["services"]
        ]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names
        # Hardware should not be included as it's from purpose2 (February)

    def test_get_service_types_distribution(
        self, test_client: TestClient, setup_test_data
    ):
        """Test service types distribution endpoint (live operations - excludes completed)."""

        response = test_client.get("/api/v1/analytics/service-types/distribution")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        # Only 1 service type expected since purpose2 (Equipment) is COMPLETED and gets filtered out
        assert len(data["data"]) == 1

        # Check only Consulting service type is included (purpose1 is IN_PROGRESS)
        service_type_names = [item["name"] for item in data["data"]]
        assert "Consulting" in service_type_names
        # Equipment is excluded because purpose2 has COMPLETED status

        # Check structure of service type items
        first_item = data["data"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert "count" in first_item

    def test_analytics_endpoints_with_status_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with status filter."""

        # Test with IN_PROGRESS status only
        response = test_client.get(
            "/api/v1/analytics/service-types/distribution",
            params={"status": [StatusEnum.IN_PROGRESS.value]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show consulting type (from purpose1)
        assert len(data["data"]) == 1
        service_type_names = [item["name"] for item in data["data"]]
        assert "Consulting" in service_type_names

    def test_analytics_endpoints_with_hierarchy_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with hierarchy filter."""

        center_id = setup_test_data["center"].id

        response = test_client.get(
            "/api/v1/analytics/services/quantities",
            params={"hierarchy_ids": [center_id]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should include all service types since both purposes are in the center
        assert len(data["data"]) == 2  # Consulting and Equipment service types

    def test_analytics_endpoints_with_service_type_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with service type filter."""

        service_type_id = setup_test_data["service_type1"].id

        response = test_client.get(
            "/api/v1/analytics/services/quantities",
            params={"service_type_id": [service_type_id]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show consulting service type
        assert len(data["data"]) == 1
        consulting_item = data["data"][0]
        assert consulting_item["service_type_name"] == "Consulting"

        # Check the services within the consulting type
        service_names = [
            service["service_name"] for service in consulting_item["services"]
        ]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names
        # Hardware should not be included as it's Equipment type

    def test_analytics_endpoints_with_supplier_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with supplier filter."""

        supplier_id = setup_test_data["supplier"].id

        response = test_client.get(
            "/api/v1/analytics/service-types/distribution",
            params={"supplier_ids": [supplier_id]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should include only 1 service type (Consulting) since Equipment purpose is COMPLETED and filtered out
        assert len(data["data"]) == 1
