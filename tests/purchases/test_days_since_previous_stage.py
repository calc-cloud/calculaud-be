"""Tests for days_since_previous_stage field in purchase stages."""

from datetime import date, datetime, timedelta

import pytest

from app.purchases.schemas import PurchaseResponse
from app.stage_types.schemas import StageTypeResponse
from app.stages.schemas import StageResponse


class TestDaysSincePreviousStage:
    """Test the days_since_previous_stage field calculation."""

    @pytest.fixture
    def sample_stage_type(self):
        """Create a sample stage type for testing."""
        return StageTypeResponse(
            id=1,
            name="Test Stage",
            display_name="Test Stage Display",
            description="Test Description",
            value_required=False,
            created_at=datetime.now(),
        )

    def test_priority_1_stage_uses_creation_date(self, sample_stage_type):
        """Test that priority 1 stages use purchase creation date as reference."""
        creation_date = datetime.now() - timedelta(days=5)

        stage = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value=None,
            completion_date=None,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [stage],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        assert purchase.flow_stages[0].days_since_previous_stage == 5

    def test_completed_stage_uses_completion_date(self, sample_stage_type):
        """Test that completed stages calculate days to completion date."""
        creation_date = datetime.now() - timedelta(days=10)
        completion_date = date.today() - timedelta(days=3)

        stage = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value="completed",
            completion_date=completion_date,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [stage],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        assert purchase.flow_stages[0].days_since_previous_stage == 7  # 10 - 3

    def test_higher_priority_stage_uses_previous_completion(self, sample_stage_type):
        """Test that higher priority stages use previous stage completion as reference."""
        creation_date = datetime.now() - timedelta(days=10)
        stage1_completion = date.today() - timedelta(days=4)

        stage1 = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value="completed",
            completion_date=stage1_completion,
            stage_type=sample_stage_type,
        )

        stage2 = StageResponse(
            id=2,
            purchase_id=1,
            stage_type_id=1,
            priority=2,
            value=None,
            completion_date=None,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [stage1, stage2],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        # Stage 1: 10 days from creation to completion (6 days ago)
        assert purchase.flow_stages[0].days_since_previous_stage == 6
        # Stage 2: 4 days from stage 1 completion to now
        assert purchase.flow_stages[1].days_since_previous_stage == 4

    def test_multiple_stages_same_priority(self, sample_stage_type):
        """Test calculation with multiple stages at same priority level."""
        creation_date = datetime.now() - timedelta(days=8)

        # Priority 1 stages - both completed
        stage1a = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value="completed",
            completion_date=date.today() - timedelta(days=5),
            stage_type=sample_stage_type,
        )

        stage1b = StageResponse(
            id=2,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value="completed",
            completion_date=date.today() - timedelta(days=3),  # Most recent
            stage_type=sample_stage_type,
        )

        # Priority 2 stage
        stage2 = StageResponse(
            id=3,
            purchase_id=1,
            stage_type_id=1,
            priority=2,
            value=None,
            completion_date=None,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [[stage1a, stage1b], stage2],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)

        # Priority 1 stages use creation date
        assert purchase.flow_stages[0][0].days_since_previous_stage == 3  # 8 - 5
        assert purchase.flow_stages[0][1].days_since_previous_stage == 5  # 8 - 3

        # Priority 2 stage uses most recent completion from priority 1 (3 days ago)
        assert purchase.flow_stages[1].days_since_previous_stage == 3

    def test_missing_previous_priority_returns_none(self, sample_stage_type):
        """Test that missing previous priority stages return None."""
        creation_date = datetime.now() - timedelta(days=5)

        # Priority 3 stage with no priority 1 or 2
        stage = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=3,
            value=None,
            completion_date=None,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [stage],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        assert purchase.flow_stages[0].days_since_previous_stage is None

    def test_no_completed_previous_priority_returns_none(self, sample_stage_type):
        """Test that uncompleted previous priority stages return None."""
        creation_date = datetime.now() - timedelta(days=5)

        stage1 = StageResponse(
            id=1,
            purchase_id=1,
            stage_type_id=1,
            priority=1,
            value=None,
            completion_date=None,  # Not completed
            stage_type=sample_stage_type,
        )

        stage2 = StageResponse(
            id=2,
            purchase_id=1,
            stage_type_id=1,
            priority=2,
            value=None,
            completion_date=None,
            stage_type=sample_stage_type,
        )

        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": creation_date,
            "costs": [],
            "flow_stages": [stage1, stage2],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        assert purchase.flow_stages[0].days_since_previous_stage == 5
        assert purchase.flow_stages[1].days_since_previous_stage is None

    def test_empty_flow_stages(self):
        """Test that empty flow_stages doesn't cause errors."""
        purchase_data = {
            "id": 1,
            "purpose_id": 1,
            "creation_date": datetime.now(),
            "costs": [],
            "flow_stages": [],
        }

        purchase = PurchaseResponse.model_validate(purchase_data)
        assert purchase.flow_stages == []
