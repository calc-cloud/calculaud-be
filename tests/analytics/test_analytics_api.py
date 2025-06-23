from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.costs.models import Cost, CurrencyEnum
from app.emfs.models import EMF
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
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

        # Create EMFs
        emf1 = EMF(emf_id="EMF001", purpose_id=purpose1.id)
        emf2 = EMF(emf_id="EMF002", purpose_id=purpose2.id)
        db_session.add_all([emf1, emf2])
        db_session.flush()

        # Create costs
        cost1 = Cost(emf_id=emf1.id, currency=CurrencyEnum.ILS, amount=1000.0)
        cost2 = Cost(emf_id=emf1.id, currency=CurrencyEnum.SUPPORT_USD, amount=200.0)
        cost3 = Cost(emf_id=emf2.id, currency=CurrencyEnum.ILS, amount=1500.0)
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

        assert "labels" in data
        assert "data" in data
        assert len(data["labels"]) == 3
        assert len(data["data"]) == 3

        # Check that services are included
        assert "IT Consulting" in data["labels"]
        assert "Software License" in data["labels"]
        assert "Hardware" in data["labels"]

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
        assert len(data["labels"]) == 2
        assert "IT Consulting" in data["labels"]
        assert "Software License" in data["labels"]
        assert "Hardware" not in data["labels"]

    def test_get_service_types_distribution(
        self, test_client: TestClient, setup_test_data
    ):
        """Test service types distribution endpoint."""

        response = test_client.get("/api/v1/analytics/service-types/distribution")

        assert response.status_code == 200
        data = response.json()

        assert "labels" in data
        assert "data" in data
        assert len(data["labels"]) == 2
        assert len(data["data"]) == 2

        # Check service types are included
        assert "Consulting" in data["labels"]
        assert "Equipment" in data["labels"]

    def test_get_expenditure_timeline_ils(
        self, test_client: TestClient, setup_test_data
    ):
        """Test expenditure timeline in ILS."""

        response = test_client.get(
            "/api/v1/analytics/expenditure/timeline",
            params={"currency": "ILS", "group_by": "month"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "labels" in data
        assert "datasets" in data
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["currency"] == "ILS"

    def test_get_expenditure_timeline_usd(
        self, test_client: TestClient, setup_test_data
    ):
        """Test expenditure timeline in USD."""

        response = test_client.get(
            "/api/v1/analytics/expenditure/timeline",
            params={"currency": "SUPPORT_USD", "group_by": "month"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "labels" in data
        assert "datasets" in data
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["currency"] == "SUPPORT_USD"

    def test_get_hierarchy_distribution_default(
        self, test_client: TestClient, setup_test_data
    ):
        """Test hierarchy distribution with default level."""

        response = test_client.get("/api/v1/analytics/hierarchies/distribution")

        assert response.status_code == 200
        data = response.json()

        assert "labels" in data
        assert "data" in data
        assert "level" in data
        assert data["level"] == "UNIT"
        assert "Test Unit" in data["labels"]

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
        assert "Test Center" in data["labels"]

    def test_analytics_endpoints_with_status_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with status filter."""

        # Test with IN_PROGRESS status only
        response = test_client.get(
            "/api/v1/analytics/service-types/distribution",
            params={"status": ["IN_PROGRESS"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show consulting type (from purpose1)
        assert len(data["labels"]) == 1
        assert "Consulting" in data["labels"]

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
        assert len(data["labels"]) == 3

    def test_analytics_endpoints_with_service_type_filter(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with service type filter."""

        service_type_id = setup_test_data["service_type1"].id

        response = test_client.get(
            "/api/v1/analytics/services/quantities",
            params={"service_type_ids": [service_type_id]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show consulting services
        assert len(data["labels"]) == 2
        assert "IT Consulting" in data["labels"]
        assert "Software License" in data["labels"]
        assert "Hardware" not in data["labels"]

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
        assert len(data["labels"]) == 2

    def test_analytics_endpoints_invalid_parameters(
        self, test_client: TestClient, setup_test_data
    ):
        """Test analytics endpoints with invalid parameters."""

        # Test invalid currency
        response = test_client.get(
            "/api/v1/analytics/expenditure/timeline",
            params={"currency": "INVALID", "group_by": "month"},
        )
        assert response.status_code == 422

        # Test invalid hierarchy level
        response = test_client.get(
            "/api/v1/analytics/hierarchies/distribution", params={"level": "INVALID"}
        )
        assert response.status_code == 422

        # Test invalid date format
        response = test_client.get(
            "/api/v1/analytics/services/quantities",
            params={"start_date": "invalid-date"},
        )
        assert response.status_code == 422
