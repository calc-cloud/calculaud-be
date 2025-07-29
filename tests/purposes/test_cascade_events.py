"""Tests for Purpose.last_modified cascade events."""

from sqlalchemy.orm import Session

from app.costs.models import Cost, CurrencyEnum
from app.purchases.models import Purchase
from app.purposes.models import Purpose, PurposeContent
from app.stage_types.models import StageType
from app.stages.models import Stage


class TestCascadeEvents:
    """Test Purpose.last_modified updates when related models change."""

    def test_purchase_create_updates_purpose_last_modified(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that creating a Purchase updates Purpose.last_modified."""
        initial_last_modified = sample_purpose.last_modified

        # Create a purchase
        purchase = Purchase(purpose_id=sample_purpose.id)
        db_session.add(purchase)
        db_session.commit()

        # Check purpose last_modified was updated
        db_session.refresh(sample_purpose)
        assert sample_purpose.last_modified > initial_last_modified

    def test_stage_create_updates_purpose_last_modified(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that creating a Stage updates Purpose.last_modified."""
        # Create stage type and purchase
        stage_type = StageType(
            name="approval",
            display_name="Approval Stage",
            description="Test approval stage",
        )
        db_session.add(stage_type)
        db_session.flush()

        purchase = Purchase(purpose_id=sample_purpose.id)
        db_session.add(purchase)
        db_session.commit()

        initial_last_modified = sample_purpose.last_modified

        # Create stage
        stage = Stage(stage_type_id=stage_type.id, purchase_id=purchase.id, priority=1)
        db_session.add(stage)
        db_session.commit()

        # Check purpose last_modified was updated
        db_session.refresh(sample_purpose)
        assert sample_purpose.last_modified > initial_last_modified

    def test_cost_create_updates_purpose_last_modified(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that creating a Cost updates Purpose.last_modified."""
        # Create purchase
        purchase = Purchase(purpose_id=sample_purpose.id)
        db_session.add(purchase)
        db_session.commit()

        initial_last_modified = sample_purpose.last_modified

        # Create cost
        cost = Cost(
            purchase_id=purchase.id,
            currency=CurrencyEnum.SUPPORT_USD,
            amount=1000.0,
        )
        db_session.add(cost)
        db_session.commit()

        # Check purpose last_modified was updated
        db_session.refresh(sample_purpose)
        assert sample_purpose.last_modified > initial_last_modified

    def test_purpose_content_create_updates_purpose_last_modified(
        self, db_session: Session, sample_purpose: Purpose, sample_service
    ):
        """Test that creating PurposeContent updates Purpose.last_modified."""
        initial_last_modified = sample_purpose.last_modified

        # Create purpose content
        content = PurposeContent(
            purpose_id=sample_purpose.id, service_id=sample_service.id, quantity=5
        )
        db_session.add(content)
        db_session.commit()

        # Check purpose last_modified was updated
        db_session.refresh(sample_purpose)
        assert sample_purpose.last_modified > initial_last_modified

    def test_purchase_update_updates_purpose_last_modified(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that updating a Purchase updates Purpose.last_modified."""
        # Create a purchase
        purchase = Purchase(purpose_id=sample_purpose.id)
        db_session.add(purchase)
        db_session.commit()

        # Record current timestamp after creation
        db_session.refresh(sample_purpose)
        initial_last_modified = sample_purpose.last_modified

        # Update purchase
        purchase.predefined_flow_id = 1
        db_session.commit()

        # Check purpose last_modified was updated
        db_session.refresh(sample_purpose)
        assert sample_purpose.last_modified > initial_last_modified
