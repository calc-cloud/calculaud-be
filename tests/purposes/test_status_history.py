from sqlalchemy.orm import Session

from app.purposes.models import Purpose, PurposeStatusHistory, StatusEnum
from app.purposes.schemas import PurposeUpdate


class TestPurposeStatusHistory:
    """Test purpose status change tracking functionality."""

    def test_status_change_creates_history_record(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that changing a purpose status creates a history record."""
        initial_status = sample_purpose.status
        new_status = StatusEnum.COMPLETED

        # Ensure we're testing an actual change
        assert initial_status != new_status

        # Change the status
        sample_purpose.status = new_status
        db_session.commit()

        # Check that history record was created
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == sample_purpose.id)
            .all()
        )

        assert len(history_records) == 1
        history = history_records[0]
        assert history.previous_status == initial_status
        assert history.new_status == new_status
        assert history.purpose_id == sample_purpose.id
        assert history.changed_at is not None
        assert history.changed_by is None  # No user context yet

    def test_multiple_status_changes_create_multiple_records(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that multiple status changes create multiple history records."""
        initial_status = sample_purpose.status

        # First change
        sample_purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        # Second change
        sample_purpose.status = StatusEnum.SIGNED
        db_session.commit()

        # Check that both history records were created
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == sample_purpose.id)
            .order_by(PurposeStatusHistory.changed_at)
            .all()
        )

        assert len(history_records) == 2

        # First record
        assert history_records[0].previous_status == initial_status
        assert history_records[0].new_status == StatusEnum.COMPLETED

        # Second record
        assert history_records[1].previous_status == StatusEnum.COMPLETED
        assert history_records[1].new_status == StatusEnum.SIGNED

    def test_same_status_no_history_record(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that setting the same status doesn't create a history record."""
        current_status = sample_purpose.status

        # Set the same status
        sample_purpose.status = current_status
        db_session.commit()

        # Check that no history record was created
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == sample_purpose.id)
            .all()
        )

        assert len(history_records) == 0

    def test_initial_purpose_creation_no_history(
        self,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
        sample_service_type,
    ):
        """Test that initial purpose creation doesn't create a history record."""
        purpose = Purpose(
            description="Test purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        db_session.add(purpose)
        db_session.commit()

        # Check that no history record was created for initial status
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == purpose.id)
            .all()
        )

        assert len(history_records) == 0

    def test_purpose_update_via_patch_creates_history(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that updating purpose via service creates history record."""
        from app.purposes import service

        initial_status = sample_purpose.status
        new_status = StatusEnum.COMPLETED

        # Update via service (simulating API call)
        update_data = PurposeUpdate(status=new_status)
        updated_purpose = service.patch_purpose(
            db_session, sample_purpose.id, update_data
        )

        assert updated_purpose.status == new_status

        # Check history record
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == sample_purpose.id)
            .all()
        )

        assert len(history_records) == 1
        history = history_records[0]
        assert history.previous_status == initial_status
        assert history.new_status == new_status

    def test_purpose_deletion_cascades_history(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that deleting a purpose cascades to delete history records."""
        # Create a history record first
        sample_purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        purpose_id = sample_purpose.id

        # Verify history exists
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == purpose_id)
            .all()
        )
        assert len(history_records) == 1

        # Delete the purpose
        db_session.delete(sample_purpose)
        db_session.commit()

        # Verify history was cascaded
        history_records = (
            db_session.query(PurposeStatusHistory)
            .filter(PurposeStatusHistory.purpose_id == purpose_id)
            .all()
        )
        assert len(history_records) == 0
