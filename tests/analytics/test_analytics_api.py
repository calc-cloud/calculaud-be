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
        """Test services quantities endpoint."""

        response = test_client.get("/api/v1/analytics/services/quantities")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert len(data["data"]) == 3

        # Check that services are included
        service_names = [item["name"] for item in data["data"]]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names
        assert "Hardware" in service_names

        # Check structure of service items
        first_item = data["data"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert "service_type_id" in first_item
        assert "service_type_name" in first_item
        assert "quantity" in first_item

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

        # Should only include services from January (purpose1)
        assert len(data["data"]) == 2
        service_names = [item["name"] for item in data["data"]]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names
        assert "Hardware" not in service_names

    def test_get_service_types_distribution(
        self, test_client: TestClient, setup_test_data
    ):
        """Test service types distribution endpoint."""

        response = test_client.get("/api/v1/analytics/service-types/distribution")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert len(data["data"]) == 2

        # Check service types are included
        service_type_names = [item["name"] for item in data["data"]]
        assert "Consulting" in service_type_names
        assert "Equipment" in service_type_names

        # Check structure of service type items
        first_item = data["data"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert "count" in first_item

    def test_get_expenditure_timeline_ils(
        self, test_client: TestClient, setup_test_data
    ):
        """Test expenditure timeline with service type breakdown."""

        response = test_client.get(
            "/api/v1/analytics/expenditure/timeline",
            params={"currency": "ILS", "group_by": "month"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "group_by" in data
        assert data["group_by"] == "month"
        assert len(data["items"]) > 0

        # Check structure of first item
        first_item = data["items"][0]
        assert "time_period" in first_item
        assert "total_ils" in first_item
        assert "total_usd" in first_item
        assert "data" in first_item

        # Check service type breakdown
        if first_item["data"]:
            service_type = first_item["data"][0]
            assert "service_type_id" in service_type
            assert "name" in service_type
            assert "total_ils" in service_type
            assert "total_usd" in service_type

    def test_get_expenditure_timeline_usd(
        self, test_client: TestClient, setup_test_data
    ):
        """Test expenditure timeline with different group_by parameter."""

        response = test_client.get(
            "/api/v1/analytics/expenditure/timeline",
            params={"currency": "SUPPORT_USD", "group_by": "year"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "group_by" in data
        assert data["group_by"] == "year"
        assert len(data["items"]) > 0

        # Check structure of first item
        first_item = data["items"][0]
        assert "time_period" in first_item
        assert "total_ils" in first_item
        assert "total_usd" in first_item
        assert "data" in first_item

        # Check service type breakdown
        if first_item["data"]:
            service_type = first_item["data"][0]
            assert "service_type_id" in service_type
            assert "name" in service_type
            assert "total_ils" in service_type
            assert "total_usd" in service_type

    def test_get_hierarchy_distribution_default(
        self, test_client: TestClient, setup_test_data
    ):
        """Test hierarchy distribution with default level."""

        response = test_client.get("/api/v1/analytics/hierarchies/distribution")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "level" in data
        assert data["level"] == "UNIT"
        assert len(data["items"]) > 0

        # Check that Test Unit is in the items
        unit_names = [item["name"] for item in data["items"]]
        assert "Test Unit" in unit_names

        # Verify item structure
        first_item = data["items"][0]
        assert "id" in first_item
        assert "name" in first_item
        assert "path" in first_item
        assert "type" in first_item
        assert "count" in first_item

    def test_get_hierarchy_distribution_with_level(
        self, test_client: TestClient, setup_test_data
    ):
        """Test hierarchy distribution with specific level."""

        unit_id = setup_test_data["unit"].id

        response = test_client.get(
            "/api/v1/analytics/hierarchies/distribution",
            params={"level": "CENTER", "parent_id": unit_id},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["level"] == "CENTER"
        assert data["parent_name"] == "Test Unit"

        # Check that Test Center is in the items
        center_names = [item["name"] for item in data["items"]]
        assert "Test Center" in center_names

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

        # Should include all services since both purposes are in the center
        assert len(data["data"]) == 3

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

        # Should only show consulting services
        assert len(data["data"]) == 2
        service_names = [item["name"] for item in data["data"]]
        assert "IT Consulting" in service_names
        assert "Software License" in service_names
        assert "Hardware" not in service_names

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

        # Should include both service types since both purposes use this supplier
        assert len(data["data"]) == 2
