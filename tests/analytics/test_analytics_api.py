from calendar import monthrange
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.costs.models import Cost, CurrencyEnum
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.purchases.models import Purchase
from app.purposes.models import (
    Purpose,
    PurposeContent,
    PurposeStatusHistory,
    StatusEnum,
)
from app.service_types.models import ServiceType
from app.services.models import Service
from app.stage_types.models import StageType
from app.stages.models import Stage
from app.suppliers.models import Supplier


def _assert_processing_time_response(
    data: dict,
    expected_total_purposes: int = None,
    expected_service_types: list[str] = None,
):
    """Helper method to validate processing time response structure and content."""
    # Check basic response structure
    assert "service_types" in data
    assert "total_purposes" in data

    # Check total purposes if specified
    if expected_total_purposes is not None:
        assert data["total_purposes"] == expected_total_purposes

    # Check service types if specified
    if expected_service_types is not None:
        actual_service_types = [
            item["service_type_name"] for item in data["service_types"]
        ]
        assert set(actual_service_types) == set(expected_service_types)

    # Validate service type structure for each item
    for service_type_item in data["service_types"]:
        assert "service_type_id" in service_type_item
        assert "service_type_name" in service_type_item
        assert "count" in service_type_item
        assert "average_processing_days" in service_type_item
        assert "min_processing_days" in service_type_item
        assert "max_processing_days" in service_type_item

        # Validate that processing days are reasonable
        assert service_type_item["average_processing_days"] >= 0
        assert service_type_item["min_processing_days"] >= 0
        assert service_type_item["max_processing_days"] >= 0
        assert service_type_item["count"] > 0


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
            status=StatusEnum.IN_PROGRESS,  # Start as IN_PROGRESS to avoid trigger creating completion record
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
        db_session.flush()

        # Create EMF stage type for processing time tests
        emf_stage_type = StageType(
            name="emf_id",
            display_name="EMF ID",
            description="EMF ID Stage for processing time tracking",
        )
        db_session.add(emf_stage_type)
        db_session.flush()

        # Create EMF stages for both purchases with known dates
        emf_stage1 = Stage(
            stage_type_id=emf_stage_type.id,
            purchase_id=purchase1.id,
            priority=1,
            value="EMF001",
            completion_date=date(2024, 1, 10),  # 5 days before purpose creation
        )
        emf_stage2 = Stage(
            stage_type_id=emf_stage_type.id,
            purchase_id=purchase2.id,
            priority=1,
            value="EMF002",
            completion_date=date(2024, 2, 10),  # 5 days before purpose creation
        )
        db_session.add_all([emf_stage1, emf_stage2])
        db_session.flush()

        # Create status history for purpose2 completion with specific test date
        status_history = PurposeStatusHistory(
            purpose_id=purpose2.id,
            previous_status=StatusEnum.IN_PROGRESS,
            new_status=StatusEnum.COMPLETED,
            changed_at=datetime(2024, 2, 25, 14, 30, 0),  # 10 days after creation
        )
        db_session.add(status_history)
        db_session.flush()  # Ensure status history is created first

        # Update purpose2 status directly in the database to avoid triggering event listeners
        from sqlalchemy import text

        db_session.execute(
            text("UPDATE purpose SET status = :status WHERE id = :purpose_id"),
            {"status": StatusEnum.COMPLETED.value, "purpose_id": purpose2.id},
        )

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
            "purchase1": purchase1,
            "purchase2": purchase2,
            "emf_stage_type": emf_stage_type,
            "emf_stage1": emf_stage1,
            "emf_stage2": emf_stage2,
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

    def test_purpose_processing_time_distribution(
        self, test_client: TestClient, setup_test_data, db_session: Session
    ):
        """Test purpose processing time distribution endpoint."""

        # Calculate expected processing time: completion date (2024-02-25) - EMF start date (2024-02-10)
        test_completion_date = datetime(2024, 2, 25, 14, 30, 0)
        emf_completion_date = setup_test_data["emf_stage2"].completion_date
        expected_days = (test_completion_date.date() - emf_completion_date).days

        response = test_client.get("/api/v1/analytics/purposes/processing-times")

        assert response.status_code == 200
        data = response.json()

        # Validate using helper method - should have 1 Equipment purpose with processing time
        _assert_processing_time_response(
            data, expected_total_purposes=1, expected_service_types=["Equipment"]
        )

        # Verify specific processing time calculation matches actual event listener behavior
        equipment_data = data["service_types"][0]
        assert equipment_data["service_type_name"] == "Equipment"
        assert equipment_data["count"] == 1

        # The expected days should be 15: (2024-02-25) - (2024-02-10) = 15 days
        assert (
            expected_days == 15
        ), f"Test setup error: expected 15 days but got {expected_days}"
        assert equipment_data["average_processing_days"] == float(expected_days)
        assert equipment_data["min_processing_days"] == expected_days
        assert equipment_data["max_processing_days"] == expected_days

    def test_purpose_processing_time_distribution_with_date_filter(
        self, test_client: TestClient, setup_test_data, db_session: Session
    ):
        """Test purpose processing time distribution with date filtering."""

        # Query actual completion date to set proper date filter
        actual_completion = db_session.execute(
            select(PurposeStatusHistory.changed_at)
            .where(PurposeStatusHistory.purpose_id == setup_test_data["purpose2"].id)
            .where(PurposeStatusHistory.new_status == StatusEnum.COMPLETED)
            .order_by(PurposeStatusHistory.changed_at.desc())
            .limit(1)
        ).scalar_one()

        start_date = f"{actual_completion.year}-{actual_completion.month:02d}-01"
        last_day = monthrange(actual_completion.year, actual_completion.month)[1]
        end_date = (
            f"{actual_completion.year}-{actual_completion.month:02d}-{last_day:02d}"
        )

        response = test_client.get(
            "/api/v1/analytics/purposes/processing-times",
            params={"start_date": start_date, "end_date": end_date},
        )

        assert response.status_code == 200
        data = response.json()

        # Should include purpose2 which completed in the filtered month
        _assert_processing_time_response(
            data,
            expected_total_purposes=1,
            expected_service_types=["Equipment"],
        )

    def test_purpose_processing_time_distribution_empty_result(
        self, test_client: TestClient, setup_test_data
    ):
        """Test purpose processing time distribution when no data matches criteria."""

        # Filter by future dates where no completions occurred
        response = test_client.get(
            "/api/v1/analytics/purposes/processing-times",
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty result - no purposes completed in 2025
        _assert_processing_time_response(
            data,
            expected_total_purposes=0,
        )
        assert data["service_types"] == []
