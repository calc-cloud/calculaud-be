"""Test pending authority functionality for purposes."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import ResponsibleAuthority, Stage, StageType
from app.config import settings


class TestPendingAuthority:
    """Test pending authority calculation and filtering for purposes."""

    @pytest.fixture
    def setup_pending_authority_data(
        self,
        db_session: Session,
        sample_purpose,
        sample_purchase,
    ):
        # Create responsible authorities first
        authority_finance = ResponsibleAuthority(
            name="Finance Department", description="Finance team"
        )
        authority_legal = ResponsibleAuthority(
            name="Legal Department", description="Legal team"
        )
        authority_procurement = ResponsibleAuthority(
            name="Procurement Department", description="Procurement team"
        )

        db_session.add(authority_finance)
        db_session.add(authority_legal)
        db_session.add(authority_procurement)
        db_session.flush()

        # Create stage types with responsible authorities
        stage_type_finance = StageType(
            name="finance_approval",
            display_name="Finance Approval",
            description="Finance team approval",
            responsible_authority_id=authority_finance.id,
            value_required=False,
        )
        stage_type_legal = StageType(
            name="legal_review",
            display_name="Legal Review",
            description="Legal team review",
            responsible_authority_id=authority_legal.id,
            value_required=False,
        )
        stage_type_procurement = StageType(
            name="procurement",
            display_name="Procurement",
            description="Procurement process",
            responsible_authority_id=authority_procurement.id,
            value_required=False,
        )

        db_session.add(stage_type_finance)
        db_session.add(stage_type_legal)
        db_session.add(stage_type_procurement)
        db_session.flush()

        # Create stages with different priorities
        # Priority 1: Finance (incomplete) - this should be the pending authority
        stage_finance = Stage(
            stage_type_id=stage_type_finance.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value=None,
            completion_date=None,
        )

        # Priority 2: Legal (incomplete) - this should NOT be pending since priority 1 exists
        stage_legal = Stage(
            stage_type_id=stage_type_legal.id,
            purchase_id=sample_purchase.id,
            priority=2,
            value=None,
            completion_date=None,
        )

        # Priority 3: Procurement (incomplete)
        stage_procurement = Stage(
            stage_type_id=stage_type_procurement.id,
            purchase_id=sample_purchase.id,
            priority=3,
            value=None,
            completion_date=None,
        )

        db_session.add(stage_finance)
        db_session.add(stage_legal)
        db_session.add(stage_procurement)
        db_session.commit()

        return {
            "purpose": sample_purpose,
            "purchase": sample_purchase,
            "authorities": {
                "finance": authority_finance,
                "legal": authority_legal,
                "procurement": authority_procurement,
            },
            "stage_types": {
                "finance": stage_type_finance,
                "legal": stage_type_legal,
                "procurement": stage_type_procurement,
            },
            "stages": {
                "finance": stage_finance,
                "legal": stage_legal,
                "procurement": stage_procurement,
            },
        }

    def test_purpose_with_pending_authority_display(
        self, test_client: TestClient, setup_pending_authority_data
    ):
        """Test that purpose displays correct pending authority."""
        purpose_id = setup_pending_authority_data["purpose"].id

        # Get single purpose
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200

        purpose_data = response.json()
        assert purpose_data["pending_authority"]["name"] == "Finance Department"

    def test_purposes_list_with_pending_authority(
        self, test_client: TestClient, setup_pending_authority_data
    ):
        """Test that purposes list includes pending authority."""
        response = test_client.get(f"{settings.api_v1_prefix}/purposes")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1

        # Find our test purpose
        test_purpose = None
        for purpose in data["items"]:
            if purpose["id"] == setup_pending_authority_data["purpose"].id:
                test_purpose = purpose
                break

        assert test_purpose is not None
        assert test_purpose["pending_authority"]["name"] == "Finance Department"

    def test_filter_by_pending_authority_single(
        self, test_client: TestClient, setup_pending_authority_data
    ):
        """Test filtering by single pending authority."""
        finance_authority_id = setup_pending_authority_data["authorities"]["finance"].id
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?pending_authority_id={finance_authority_id}"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1

        # All returned purposes should have Finance Department as pending authority
        for purpose in data["items"]:
            if purpose["pending_authority"] is not None:
                assert purpose["pending_authority"]["name"] == "Finance Department"

    def test_filter_by_pending_authority_multiple(
        self, test_client: TestClient, setup_pending_authority_data
    ):
        """Test filtering by multiple pending authorities."""
        finance_authority_id = setup_pending_authority_data["authorities"]["finance"].id
        legal_authority_id = setup_pending_authority_data["authorities"]["legal"].id
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?"
            f"pending_authority_id={finance_authority_id}&"
            f"pending_authority_id={legal_authority_id}"
        )
        assert response.status_code == 200

        data = response.json()
        # Should include our test purpose
        purpose_ids = [p["id"] for p in data["items"]]
        assert setup_pending_authority_data["purpose"].id in purpose_ids

    def test_filter_by_nonexistent_pending_authority(
        self, test_client: TestClient, setup_pending_authority_data
    ):
        """Test filtering by non-existent pending authority returns empty."""
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?pending_authority_id=99999"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_pending_authority_with_completed_lowest_priority(
        self,
        db_session: Session,
        test_client: TestClient,
        setup_pending_authority_data,
    ):
        """Test that completing lowest priority stage changes pending authority."""

        # Complete the finance stage (priority 1)
        finance_stage = setup_pending_authority_data["stages"]["finance"]
        finance_stage.completion_date = date.today()
        db_session.commit()

        purpose_id = setup_pending_authority_data["purpose"].id

        # Get purpose - should now show Legal Department as pending authority
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200

        purpose_data = response.json()
        assert purpose_data["pending_authority"]["name"] == "Legal Department"

    def test_pending_authority_all_stages_completed(
        self,
        db_session: Session,
        test_client: TestClient,
        setup_pending_authority_data,
    ):
        """Test that completing all stages results in null pending authority."""
        from datetime import date

        # Complete all stages
        for stage in setup_pending_authority_data["stages"].values():
            stage.completion_date = date.today()
        db_session.commit()

        purpose_id = setup_pending_authority_data["purpose"].id

        # Get purpose - should now show null pending authority
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200

        purpose_data = response.json()
        assert purpose_data["pending_authority"] is None

    def test_pending_authority_no_stages(self, test_client: TestClient, sample_purpose):
        """Test that purpose with no stages has null pending authority."""
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{sample_purpose.id}"
        )
        assert response.status_code == 200

        purpose_data = response.json()
        assert purpose_data["pending_authority"] is None

    def test_pending_authority_multiple_stages_same_priority(
        self,
        db_session: Session,
        test_client: TestClient,
        sample_purpose,
        sample_purchase,
    ):
        """Test deterministic selection when multiple stages at same priority."""

        # Create responsible authorities first
        authority_a = ResponsibleAuthority(
            name="Department A", description="Department A"
        )
        authority_b = ResponsibleAuthority(
            name="Department B", description="Department B"
        )

        db_session.add(authority_a)
        db_session.add(authority_b)
        db_session.flush()

        # Create two stage types with different responsible authorities
        stage_type_a = StageType(
            name="approval_a",
            display_name="Approval A",
            responsible_authority_id=authority_a.id,
            value_required=False,
        )
        stage_type_b = StageType(
            name="approval_b",
            display_name="Approval B",
            responsible_authority_id=authority_b.id,
            value_required=False,
        )

        db_session.add(stage_type_a)
        db_session.add(stage_type_b)
        db_session.flush()

        # Create two stages at same priority
        stage_a = Stage(
            stage_type_id=stage_type_a.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value=None,
            completion_date=None,
        )
        stage_b = Stage(
            stage_type_id=stage_type_b.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value=None,
            completion_date=None,
        )

        db_session.add(stage_a)
        db_session.add(stage_b)
        db_session.commit()

        # Get purpose - should consistently pick one authority (based on stage_type.id ordering)
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{sample_purpose.id}"
        )
        assert response.status_code == 200

        purpose_data = response.json()
        pending_authority = purpose_data["pending_authority"]
        assert pending_authority["name"] in ["Department A", "Department B"]

        # Call multiple times to ensure consistency
        for _ in range(3):
            response = test_client.get(
                f"{settings.api_v1_prefix}/purposes/{sample_purpose.id}"
            )
            assert response.status_code == 200
            assert (
                response.json()["pending_authority"]["name"]
                == pending_authority["name"]
            )

    def test_pending_authority_null_responsible_authority_ignored(
        self,
        db_session: Session,
        test_client: TestClient,
        sample_purpose,
        sample_purchase,
    ):
        """Test that stages with null responsible_authority are ignored."""

        # Create responsible authority for valid stage type
        authority_valid = ResponsibleAuthority(
            name="Valid Department", description="Valid department"
        )

        db_session.add(authority_valid)
        db_session.flush()

        # Create stage type with null responsible authority
        stage_type_null = StageType(
            name="null_authority",
            display_name="Null Authority",
            responsible_authority_id=None,
            value_required=False,
        )

        # Create stage type with responsible authority
        stage_type_valid = StageType(
            name="valid_authority",
            display_name="Valid Authority",
            responsible_authority_id=authority_valid.id,
            value_required=False,
        )

        db_session.add(stage_type_null)
        db_session.add(stage_type_valid)
        db_session.flush()

        # Create stages - null authority at priority 1, valid at priority 2
        stage_null = Stage(
            stage_type_id=stage_type_null.id,
            purchase_id=sample_purchase.id,
            priority=1,
            value=None,
            completion_date=None,
        )
        stage_valid = Stage(
            stage_type_id=stage_type_valid.id,
            purchase_id=sample_purchase.id,
            priority=2,
            value=None,
            completion_date=None,
        )

        db_session.add(stage_null)
        db_session.add(stage_valid)
        db_session.commit()

        # Get purpose - should show Valid Department (skipping null authority)
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{sample_purpose.id}"
        )
        assert response.status_code == 200

        purpose_data = response.json()
        assert purpose_data["pending_authority"]["name"] == "Valid Department"
