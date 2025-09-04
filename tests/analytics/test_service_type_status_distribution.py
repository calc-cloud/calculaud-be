"""Test service type status distribution functionality."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.purposes.models import Purpose, PurposeStatusHistory, StatusEnum
from app.service_types.models import ServiceType


class TestServiceTypeStatusDistribution:
    """Test service type status distribution analytics."""

    def test_basic_status_distribution(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_service_type,
        sample_supplier,
    ):
        """Test basic status distribution functionality."""
        # Create a service type
        service_type = ServiceType(name="IT Services")
        db_session.add(service_type)
        db_session.flush()

        # Create a purpose with the service type
        purpose = Purpose(
            description="Test Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type.id,
        )
        db_session.add(purpose)
        db_session.commit()

        # Manually change status to COMPLETED to trigger history
        purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        # Test the endpoint
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["target_status"] == "COMPLETED"
        assert data["total_count"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["service_type_name"] == "IT Services"
        assert data["data"][0]["count"] == 1

    def test_multiple_service_types(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
    ):
        """Test distribution across multiple service types."""
        # Create multiple service types
        service_type_1 = ServiceType(name="IT Services")
        service_type_2 = ServiceType(name="Consulting")
        db_session.add_all([service_type_1, service_type_2])
        db_session.flush()

        # Create purposes with different service types
        purpose_1 = Purpose(
            description="IT Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_1.id,
        )
        purpose_2 = Purpose(
            description="Consulting Purpose 1",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_2.id,
        )
        purpose_3 = Purpose(
            description="Consulting Purpose 2",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_2.id,
        )
        db_session.add_all([purpose_1, purpose_2, purpose_3])
        db_session.commit()

        # Change all to COMPLETED
        for purpose in [purpose_1, purpose_2, purpose_3]:
            purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        # Test the endpoint
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["target_status"] == "COMPLETED"
        assert data["total_count"] == 3

        # Should be sorted by service type name
        assert len(data["data"]) == 2
        assert data["data"][0]["service_type_name"] == "Consulting"
        assert data["data"][0]["count"] == 2
        assert data["data"][1]["service_type_name"] == "IT Services"
        assert data["data"][1]["count"] == 1

    def test_latest_status_change_only(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
        sample_service_type,
    ):
        """Test that only the latest status change is counted."""
        # Create a purpose
        purpose = Purpose(
            description="Test Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        db_session.add(purpose)
        db_session.commit()

        # Create multiple status changes: IN_PROGRESS -> COMPLETED -> SIGNED -> COMPLETED
        base_time = datetime.now() - timedelta(days=10)

        # First change to COMPLETED
        purpose.status = StatusEnum.COMPLETED
        db_session.commit()
        # Update the timestamp manually for the first change
        first_history = (
            db_session.query(PurposeStatusHistory)
            .filter_by(purpose_id=purpose.id, new_status=StatusEnum.COMPLETED)
            .first()
        )
        first_history.changed_at = base_time + timedelta(days=1)

        # Change to SIGNED
        purpose.status = StatusEnum.SIGNED
        db_session.commit()
        signed_history = (
            db_session.query(PurposeStatusHistory)
            .filter_by(purpose_id=purpose.id, new_status=StatusEnum.SIGNED)
            .first()
        )
        signed_history.changed_at = base_time + timedelta(days=2)

        # Change back to COMPLETED (this should be the latest)
        purpose.status = StatusEnum.COMPLETED
        db_session.commit()
        second_history = (
            db_session.query(PurposeStatusHistory)
            .filter_by(purpose_id=purpose.id, new_status=StatusEnum.COMPLETED)
            .order_by(PurposeStatusHistory.changed_at.desc())
            .first()
        )
        second_history.changed_at = base_time + timedelta(days=3)

        db_session.commit()

        # Test the endpoint - should only count the latest COMPLETED change
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["target_status"] == "COMPLETED"
        assert (
            data["total_count"] == 1
        )  # Only the latest COMPLETED change should be counted
        assert len(data["data"]) == 1

    def test_date_filtering(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
        sample_service_type,
    ):
        """Test filtering by date range."""
        # Create two purposes
        purpose_1 = Purpose(
            description="Early Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        purpose_2 = Purpose(
            description="Late Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        db_session.add_all([purpose_1, purpose_2])
        db_session.commit()

        # Change both to COMPLETED but at different times
        base_date = datetime(2024, 1, 1)

        purpose_1.status = StatusEnum.COMPLETED
        db_session.commit()
        early_history = (
            db_session.query(PurposeStatusHistory)
            .filter_by(purpose_id=purpose_1.id, new_status=StatusEnum.COMPLETED)
            .first()
        )
        early_history.changed_at = base_date

        purpose_2.status = StatusEnum.COMPLETED
        db_session.commit()
        late_history = (
            db_session.query(PurposeStatusHistory)
            .filter_by(purpose_id=purpose_2.id, new_status=StatusEnum.COMPLETED)
            .first()
        )
        late_history.changed_at = base_date + timedelta(days=40)

        db_session.commit()

        # Test without date filtering - should get both
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

        # Test with date filtering - should get only the early one
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        response = test_client.get(
            f"/api/v1/analytics/service-types/COMPLETED/distribution"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_service_type_filtering(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
    ):
        """Test filtering by service type IDs."""
        # Create multiple service types
        service_type_1 = ServiceType(name="IT Services")
        service_type_2 = ServiceType(name="Consulting")
        service_type_3 = ServiceType(name="Marketing")
        db_session.add_all([service_type_1, service_type_2, service_type_3])
        db_session.flush()

        # Create purposes with different service types
        purposes = []
        for i, service_type in enumerate(
            [service_type_1, service_type_2, service_type_3]
        ):
            purpose = Purpose(
                description=f"Purpose {i}",
                status=StatusEnum.IN_PROGRESS,
                hierarchy_id=sample_hierarchy.id,
                supplier_id=sample_supplier.id,
                service_type_id=service_type.id,
            )
            purposes.append(purpose)
            db_session.add(purpose)
        db_session.commit()

        # Change all to COMPLETED
        for purpose in purposes:
            purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        # Test without filtering - should get all 3
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        assert len(data["data"]) == 3

        # Test filtering by specific service types - should get only 2
        response = test_client.get(
            f"/api/v1/analytics/service-types/COMPLETED/distribution"
            f"?service_type_id={service_type_1.id}&service_type_id={service_type_2.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["data"]) == 2

        service_type_names = {item["service_type_name"] for item in data["data"]}
        assert service_type_names == {"IT Services", "Consulting"}

    def test_no_matching_status_changes(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
        sample_service_type,
    ):
        """Test endpoint when no purposes have the target status change."""
        # Create a purpose but don't change its status to COMPLETED
        purpose = Purpose(
            description="Test Purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        db_session.add(purpose)
        db_session.commit()

        # Test for COMPLETED status - should return empty results
        response = test_client.get(
            "/api/v1/analytics/service-types/COMPLETED/distribution"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["target_status"] == "COMPLETED"
        assert data["total_count"] == 0
        assert data["data"] == []

    def test_invalid_status_enum(self, test_client: TestClient):
        """Test endpoint with invalid status enum."""
        response = test_client.get(
            "/api/v1/analytics/service-types/INVALID_STATUS/distribution"
        )
        assert response.status_code == 422  # Validation error

    def test_combined_filtering(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
    ):
        """Test combining date and service type filtering."""
        # Create two service types
        service_type_1 = ServiceType(name="IT Services")
        service_type_2 = ServiceType(name="Consulting")
        db_session.add_all([service_type_1, service_type_2])
        db_session.flush()

        # Create purposes with different service types and dates
        purpose_1 = Purpose(
            description="IT Purpose Early",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_1.id,
        )
        purpose_2 = Purpose(
            description="IT Purpose Late",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_1.id,
        )
        purpose_3 = Purpose(
            description="Consulting Purpose Early",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=service_type_2.id,
        )
        db_session.add_all([purpose_1, purpose_2, purpose_3])
        db_session.commit()

        # Change all to COMPLETED with different timestamps
        base_date = datetime(2024, 1, 1)
        purposes_and_dates = [
            (purpose_1, base_date),  # Early IT
            (purpose_2, base_date + timedelta(days=40)),  # Late IT
            (purpose_3, base_date),  # Early Consulting
        ]

        for purpose, target_date in purposes_and_dates:
            purpose.status = StatusEnum.COMPLETED
            db_session.commit()
            history = (
                db_session.query(PurposeStatusHistory)
                .filter_by(purpose_id=purpose.id, new_status=StatusEnum.COMPLETED)
                .first()
            )
            history.changed_at = target_date

        db_session.commit()

        # Test combined filtering: only IT Services in January
        response = test_client.get(
            f"/api/v1/analytics/service-types/COMPLETED/distribution"
            f"?start_date=2024-01-01&end_date=2024-01-31&service_type_id={service_type_1.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["service_type_name"] == "IT Services"
        assert data["data"][0]["count"] == 1
