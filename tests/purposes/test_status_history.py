from sqlalchemy import select
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

        # Check that history records were created
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory)
                .where(PurposeStatusHistory.purpose_id == sample_purpose.id)
                .order_by(PurposeStatusHistory.changed_at)
            )
            .scalars()
            .all()
        )

        # Now we have 2 records: initial creation + status change
        assert len(history_records) == 2

        # First record is initial creation
        initial_history = history_records[0]
        assert initial_history.previous_status is None
        assert initial_history.new_status == initial_status

        # Second record is the status change
        change_history = history_records[1]
        assert change_history.previous_status == initial_status
        assert change_history.new_status == new_status
        assert change_history.purpose_id == sample_purpose.id
        assert change_history.changed_at is not None
        assert change_history.changed_by is None  # No user context yet

    def test_multiple_status_changes_create_multiple_records(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that multiple status changes create multiple history records."""
        # First change
        sample_purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        # Second change
        sample_purpose.status = StatusEnum.SIGNED
        db_session.commit()

        # Check that both history records were created
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory)
                .where(PurposeStatusHistory.purpose_id == sample_purpose.id)
                .order_by(PurposeStatusHistory.changed_at)
            )
            .scalars()
            .all()
        )

        # We should have initial creation + 2 status changes = 3 records
        assert len(history_records) == 3

        # First record is initial creation (from fixture)
        assert history_records[0].previous_status is None
        assert history_records[0].new_status == StatusEnum.IN_PROGRESS

        # Second record is first status change
        assert history_records[1].previous_status == StatusEnum.IN_PROGRESS
        assert history_records[1].new_status == StatusEnum.COMPLETED

        # Third record is second status change
        assert history_records[2].previous_status == StatusEnum.COMPLETED
        assert history_records[2].new_status == StatusEnum.SIGNED

    def test_same_status_no_history_record(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that setting the same status doesn't create additional history record."""
        current_status = sample_purpose.status

        # Set the same status
        sample_purpose.status = current_status
        db_session.commit()

        # Check that only initial creation history record exists (no additional record for same status)
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory).where(
                    PurposeStatusHistory.purpose_id == sample_purpose.id
                )
            )
            .scalars()
            .all()
        )

        # Only initial creation record should exist
        assert len(history_records) == 1
        assert history_records[0].previous_status is None
        assert history_records[0].new_status == current_status

    def test_initial_purpose_creation_creates_history(
        self,
        db_session: Session,
        sample_hierarchy,
        sample_supplier,
        sample_service_type,
    ):
        """Test that initial purpose creation creates a history record."""
        purpose = Purpose(
            description="Test purpose",
            status=StatusEnum.IN_PROGRESS,
            hierarchy_id=sample_hierarchy.id,
            supplier_id=sample_supplier.id,
            service_type_id=sample_service_type.id,
        )
        db_session.add(purpose)
        db_session.commit()

        # Check that history record was created for initial status
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory).where(
                    PurposeStatusHistory.purpose_id == purpose.id
                )
            )
            .scalars()
            .all()
        )

        assert len(history_records) == 1
        history = history_records[0]
        assert (
            history.previous_status is None
        )  # No previous status for initial creation
        assert history.new_status == StatusEnum.IN_PROGRESS
        assert history.purpose_id == purpose.id
        assert history.changed_at is not None
        assert history.changed_by is None

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

        # Check history records
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory)
                .where(PurposeStatusHistory.purpose_id == sample_purpose.id)
                .order_by(PurposeStatusHistory.changed_at)
            )
            .scalars()
            .all()
        )

        # Now we have 2 records: initial creation + status change
        assert len(history_records) == 2

        # First record is initial creation (from fixture)
        initial_history = history_records[0]
        assert initial_history.previous_status is None
        assert initial_history.new_status == initial_status

        # Second record is the status change
        change_history = history_records[1]
        assert change_history.previous_status == initial_status
        assert change_history.new_status == new_status

    def test_purpose_deletion_cascades_history(
        self, db_session: Session, sample_purpose: Purpose
    ):
        """Test that deleting a purpose cascades to delete history records."""
        # Create a history record first
        sample_purpose.status = StatusEnum.COMPLETED
        db_session.commit()

        purpose_id = sample_purpose.id

        # Verify history exists (initial creation + status change)
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory).where(
                    PurposeStatusHistory.purpose_id == purpose_id
                )
            )
            .scalars()
            .all()
        )
        assert len(history_records) == 2

        # Delete the purpose
        db_session.delete(sample_purpose)
        db_session.commit()

        # Verify history was cascaded
        history_records = (
            db_session.execute(
                select(PurposeStatusHistory).where(
                    PurposeStatusHistory.purpose_id == purpose_id
                )
            )
            .scalars()
            .all()
        )
        assert len(history_records) == 0
