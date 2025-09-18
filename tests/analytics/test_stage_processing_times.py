"""Tests for stage processing time analytics functionality."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.purchases.models import Purchase
from app.purposes.models import Purpose, StatusEnum
from app.service_types.models import ServiceType
from app.stage_types.models import StageType
from app.stages.models import Stage


@pytest.fixture
def sample_purpose_with_service_type(
    db_session: Session, sample_service_type: ServiceType
) -> Purpose:
    """Create a purpose with service type for analytics tests."""
    purpose = Purpose(
        description="Test purpose for analytics",
        status=StatusEnum.COMPLETED,
        service_type_id=sample_service_type.id,
        creation_time=date(2024, 1, 1),
    )
    db_session.add(purpose)
    db_session.commit()
    db_session.refresh(purpose)
    return purpose


@pytest.fixture
def sample_purchase_with_service_type(
    db_session: Session, sample_purpose_with_service_type: Purpose
) -> Purchase:
    """Create a purchase linked to purpose with service type."""
    purchase = Purchase(purpose_id=sample_purpose_with_service_type.id)
    db_session.add(purchase)
    db_session.commit()
    db_session.refresh(purchase)
    return purchase


def _assert_stage_processing_time_response(
    data: dict,
    expected_stage_types: list[str] = None,
    expected_service_types_per_stage: dict[str, list[str]] = None,
):
    """Helper method to validate stage processing time response structure and content."""
    # Check basic response structure
    assert "data" in data
    assert isinstance(data["data"], list)

    # Check stage types if specified
    if expected_stage_types is not None:
        actual_stage_types = [item["stage_type_display_name"] for item in data["data"]]
        assert set(actual_stage_types) == set(expected_stage_types)

    # Validate stage type structure for each item
    for stage_type_item in data["data"]:
        assert "stage_type_id" in stage_type_item
        assert "stage_type_name" in stage_type_item
        assert "stage_type_display_name" in stage_type_item
        assert "service_types" in stage_type_item
        assert "overall_count" in stage_type_item
        assert "overall_avg_processing_days" in stage_type_item
        assert "overall_min_processing_days" in stage_type_item
        assert "overall_max_processing_days" in stage_type_item

        # Validate service type breakdown
        for service_type_item in stage_type_item["service_types"]:
            assert "service_type_id" in service_type_item
            assert "service_type_name" in service_type_item
            assert "count" in service_type_item
            assert "avg_processing_days" in service_type_item
            assert "min_processing_days" in service_type_item
            assert "max_processing_days" in service_type_item

            # Ensure processing times are non-negative
            assert service_type_item["count"] >= 0
            assert service_type_item["avg_processing_days"] >= 0
            assert service_type_item["min_processing_days"] >= 0
            assert service_type_item["max_processing_days"] >= 0

        # Check service types for this stage if specified
        if expected_service_types_per_stage is not None:
            stage_name = stage_type_item["stage_type_display_name"]
            if stage_name in expected_service_types_per_stage:
                actual_service_types = [
                    item["service_type_name"]
                    for item in stage_type_item["service_types"]
                ]
                expected = expected_service_types_per_stage[stage_name]
                assert set(actual_service_types) == set(expected)


class TestStageProcessingTimesAPI:
    """Test stage processing time analytics API endpoints."""

    def test_get_stage_processing_times_empty_data(self, test_client: TestClient):
        """Test stage processing times with no data."""
        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)
        assert len(data["data"]) == 0

    def test_get_stage_processing_times_with_basic_data(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_service_type: ServiceType,
        sample_purchase_with_service_type: Purchase,
        required_value_stage_type: StageType,
        no_value_stage_type: StageType,
    ):
        """Test stage processing times with basic completed stages."""
        # Create stages with completion dates that follow priority logic
        base_date = date(2024, 1, 1)

        # Priority 1 stage (completed first)
        stage_1 = Stage(
            stage_type_id=required_value_stage_type.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=1,
            completion_date=base_date,
        )

        # Priority 2 stage (completed 5 days later)
        stage_2 = Stage(
            stage_type_id=no_value_stage_type.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=2,
            completion_date=base_date + timedelta(days=5),
        )

        db_session.add_all([stage_1, stage_2])
        db_session.commit()

        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have only stage_type_2 (priority > 1 and completed)
        assert len(data["data"]) == 1
        stage_data = data["data"][0]
        assert stage_data["stage_type_display_name"] == "No Value Stage"
        assert stage_data["overall_count"] == 1
        assert stage_data["overall_avg_processing_days"] == 5.0
        assert stage_data["overall_min_processing_days"] == 5
        assert stage_data["overall_max_processing_days"] == 5

        # Check service type breakdown
        assert len(stage_data["service_types"]) == 1
        service_type_data = stage_data["service_types"][0]
        assert service_type_data["service_type_name"] == sample_service_type.name
        assert service_type_data["count"] == 1
        assert service_type_data["avg_processing_days"] == 5.0

    def test_get_stage_processing_times_multiple_service_types(
        self, test_client: TestClient, db_session: Session
    ):
        """Test stage processing times with multiple service types."""
        # Create service types
        service_type_1 = ServiceType(name="Cloud Infrastructure")
        service_type_2 = ServiceType(name="Database Services")
        db_session.add_all([service_type_1, service_type_2])

        # Create stage type
        stage_type = StageType(
            name="approval", display_name="Approval", description="Approval stage"
        )
        db_session.add(stage_type)
        db_session.commit()

        # Create purposes for different service types
        base_date = date(2024, 1, 1)

        for i, service_type in enumerate([service_type_1, service_type_2]):
            purpose = Purpose(
                description=f"Test purpose {i}",
                status=StatusEnum.COMPLETED,
                service_type_id=service_type.id,
                creation_time=base_date,
            )
            db_session.add(purpose)
            db_session.commit()

            purchase = Purchase(purpose_id=purpose.id)
            db_session.add(purchase)
            db_session.commit()

            # Priority 1 stage
            stage_1 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=1,
                completion_date=base_date,
            )

            # Priority 2 stage with different processing times
            processing_days = (i + 1) * 3  # 3 days for first, 6 days for second
            stage_2 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=2,
                completion_date=base_date + timedelta(days=processing_days),
            )

            db_session.add_all([stage_1, stage_2])

        db_session.commit()

        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have one stage type with two service types
        assert len(data["data"]) == 1
        stage_data = data["data"][0]
        assert stage_data["stage_type_display_name"] == "Approval"
        assert stage_data["overall_count"] == 2
        assert stage_data["overall_avg_processing_days"] == 4.5  # (3 + 6) / 2
        assert stage_data["overall_min_processing_days"] == 3
        assert stage_data["overall_max_processing_days"] == 6

        # Check service type breakdown
        assert len(stage_data["service_types"]) == 2
        service_types_data = {
            item["service_type_name"]: item for item in stage_data["service_types"]
        }

        assert "Cloud Infrastructure" in service_types_data
        assert service_types_data["Cloud Infrastructure"]["avg_processing_days"] == 3.0

        assert "Database Services" in service_types_data
        assert service_types_data["Database Services"]["avg_processing_days"] == 6.0

    def test_get_stage_processing_times_same_priority_handling(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_service_type: ServiceType,
        sample_purchase_with_service_type: Purchase,
    ):
        """Test stage processing times with multiple stages at same priority."""
        # Create stage types
        stage_type_1 = StageType(
            name="review_1", display_name="Review 1", description="First review stage"
        )
        stage_type_2 = StageType(
            name="review_2", display_name="Review 2", description="Second review stage"
        )
        stage_type_3 = StageType(
            name="approval", display_name="Approval", description="Final approval stage"
        )
        db_session.add_all([stage_type_1, stage_type_2, stage_type_3])
        db_session.commit()

        base_date = date(2024, 1, 1)

        # Priority 1 stage
        stage_1 = Stage(
            stage_type_id=stage_type_1.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=1,
            completion_date=base_date,
        )

        # Two stages at priority 2, completed on different dates
        stage_2a = Stage(
            stage_type_id=stage_type_2.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=2,
            completion_date=base_date + timedelta(days=3),
        )

        stage_2b = Stage(
            stage_type_id=stage_type_1.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=2,
            completion_date=base_date + timedelta(days=5),  # Latest at priority 2
        )

        # Priority 3 stage should use the latest from priority 2 (day 5)
        stage_3 = Stage(
            stage_type_id=stage_type_3.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=3,
            completion_date=base_date + timedelta(days=8),
        )

        db_session.add_all([stage_1, stage_2a, stage_2b, stage_3])
        db_session.commit()

        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have stages from priority 2 and 3
        stage_names = [item["stage_type_display_name"] for item in data["data"]]
        assert "Review 2" in stage_names  # From priority 2
        assert "Approval" in stage_names  # From priority 3

        # Find approval stage and check it used latest from priority 2
        approval_stage = next(
            item
            for item in data["data"]
            if item["stage_type_display_name"] == "Approval"
        )
        # Processing time should be 8 - 5 = 3 days (from latest priority 2 completion)
        assert approval_stage["overall_avg_processing_days"] == 3.0

    def test_get_stage_processing_times_excludes_incomplete_stages(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_service_type: ServiceType,
        sample_purchase_with_service_type: Purchase,
    ):
        """Test that incomplete stages are excluded from processing time calculations."""
        # Create stage type
        stage_type = StageType(
            name="approval", display_name="Approval", description="Approval stage"
        )
        db_session.add(stage_type)
        db_session.commit()

        base_date = date(2024, 1, 1)

        # Priority 1 stage (completed)
        stage_1 = Stage(
            stage_type_id=stage_type.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=1,
            completion_date=base_date,
        )

        # Priority 2 stage (incomplete - no completion_date)
        stage_2 = Stage(
            stage_type_id=stage_type.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=2,
            completion_date=None,  # Not completed
        )

        db_session.add_all([stage_1, stage_2])
        db_session.commit()

        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have no data since stage_2 is incomplete
        assert len(data["data"]) == 0

    def test_get_stage_processing_times_with_service_type_filter(
        self, test_client: TestClient, db_session: Session
    ):
        """Test stage processing times with service type filtering."""
        # Create service types
        service_type_1 = ServiceType(name="Cloud Infrastructure")
        service_type_2 = ServiceType(name="Database Services")
        db_session.add_all([service_type_1, service_type_2])

        # Create stage type
        stage_type = StageType(
            name="approval", display_name="Approval", description="Approval stage"
        )
        db_session.add(stage_type)
        db_session.commit()

        # Create purposes for different service types
        base_date = date(2024, 1, 1)

        for i, service_type in enumerate([service_type_1, service_type_2]):
            purpose = Purpose(
                description=f"Test purpose {i}",
                status=StatusEnum.COMPLETED,
                service_type_id=service_type.id,
                creation_time=base_date,
            )
            db_session.add(purpose)
            db_session.commit()

            purchase = Purchase(purpose_id=purpose.id)
            db_session.add(purchase)
            db_session.commit()

            # Create completed stages
            stage_1 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=1,
                completion_date=base_date,
            )

            stage_2 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=2,
                completion_date=base_date + timedelta(days=3),
            )

            db_session.add_all([stage_1, stage_2])

        db_session.commit()

        # Test with service type filter
        response = test_client.get(
            f"/api/v1/analytics/stages/processing-times?service_type_id={service_type_1.id}"
        )
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have one stage type with only one service type
        assert len(data["data"]) == 1
        stage_data = data["data"][0]
        assert (
            stage_data["overall_count"] == 2
        )  # Overall count includes all service types
        assert len(stage_data["service_types"]) == 1  # But service types filtered
        assert (
            stage_data["service_types"][0]["service_type_name"]
            == "Cloud Infrastructure"
        )

    def test_get_stage_processing_times_with_date_filter(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_service_type: ServiceType,
    ):
        """Test stage processing times with date filtering."""
        # Create stage type
        stage_type = StageType(
            name="approval", display_name="Approval", description="Approval stage"
        )
        db_session.add(stage_type)
        db_session.commit()

        # Create purposes with different creation dates
        early_date = date(2024, 1, 1)
        late_date = date(2024, 2, 1)

        for i, creation_date in enumerate([early_date, late_date]):
            purpose = Purpose(
                description=f"Test purpose {i}",
                status=StatusEnum.COMPLETED,
                service_type_id=sample_service_type.id,
                creation_time=creation_date,
            )
            db_session.add(purpose)
            db_session.commit()

            purchase = Purchase(purpose_id=purpose.id)
            db_session.add(purchase)
            db_session.commit()

            # Create completed stages
            stage_1 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=1,
                completion_date=creation_date,
            )

            stage_2 = Stage(
                stage_type_id=stage_type.id,
                purchase_id=purchase.id,
                priority=2,
                completion_date=creation_date + timedelta(days=3),
            )

            db_session.add_all([stage_1, stage_2])

        db_session.commit()

        # Test with date filter to include only early date
        response = test_client.get(
            "/api/v1/analytics/stages/processing-times?start_date=2024-01-01&end_date=2024-01-15"
        )
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have one stage type with only one purpose (filtered by date)
        assert len(data["data"]) == 1
        stage_data = data["data"][0]
        assert stage_data["overall_count"] == 1

    def test_get_stage_processing_times_excludes_priority_one(
        self,
        test_client: TestClient,
        db_session: Session,
        sample_service_type: ServiceType,
        sample_purchase_with_service_type: Purchase,
    ):
        """Test that priority 1 stages are excluded from results."""
        # Create stage type
        stage_type = StageType(
            name="emf_id", display_name="EMF ID", description="Initial EMF ID stage"
        )
        db_session.add(stage_type)
        db_session.commit()

        # Create only priority 1 stage
        stage_1 = Stage(
            stage_type_id=stage_type.id,
            purchase_id=sample_purchase_with_service_type.id,
            priority=1,
            completion_date=date(2024, 1, 1),
        )

        db_session.add(stage_1)
        db_session.commit()

        response = test_client.get("/api/v1/analytics/stages/processing-times")
        assert response.status_code == 200

        data = response.json()
        _assert_stage_processing_time_response(data)

        # Should have no data since priority 1 stages are excluded
        assert len(data["data"]) == 0
