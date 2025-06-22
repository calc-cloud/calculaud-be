from fastapi.testclient import TestClient

from app.config import settings


class TestPurposesAPI:
    """Test Purpose API endpoints."""

    def test_get_purposes_empty_list(self, test_client: TestClient):
        """Test GET /purposes returns empty list initially."""
        response = test_client.get(f"{settings.api_v1_prefix}/purposes")
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "has_next": False,
            "has_prev": False,
            "pages": 0,
        }

    def test_create_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test POST /purposes creates new purpose."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["hierarchy"]["id"] == sample_purpose_data["hierarchy_id"]
        assert data["description"] == sample_purpose_data["description"]
        assert data["status"] == sample_purpose_data["status"]
        assert "id" in data
        assert "creation_time" in data

    def test_get_purpose_by_id(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes/{id} returns purpose with EMFs and costs."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Get purpose by ID
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == purpose_id
        assert data["description"] == sample_purpose_data["description"]
        assert "emfs" in data
        assert isinstance(data["emfs"], list)

    def test_get_purpose_not_found(self, test_client: TestClient):
        """Test GET /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/999")
        assert response.status_code == 404

    def test_patch_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test PATCH /purposes/{id} patches purpose."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Patch purpose
        patch_data = sample_purpose_data.copy()
        patch_data["description"] = "Patched description"
        patch_data["status"] = "IN_PROGRESS"

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=patch_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Patched description"
        assert data["status"] == "IN_PROGRESS"
        assert data["id"] == purpose_id

    def test_patch_purpose_not_found(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test PATCH /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/999", json=sample_purpose_data
        )
        assert response.status_code == 404

    def test_delete_purpose(self, test_client: TestClient, sample_purpose_data: dict):
        """Test DELETE /purposes/{id} deletes purpose."""
        # Create purpose first
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data
        )
        purpose_id = create_response.json()["id"]

        # Delete purpose
        response = test_client.delete(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 204

        # Verify purpose is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert get_response.status_code == 404

    def test_delete_purpose_not_found(self, test_client: TestClient):
        """Test DELETE /purposes/{id} returns 404 for non-existent purpose."""
        response = test_client.delete(f"{settings.api_v1_prefix}/purposes/999")
        assert response.status_code == 404

    def test_get_purposes_with_pagination(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with pagination parameters."""
        # Create multiple purposes
        for i in range(5):
            data = sample_purpose_data.copy()
            data["description"] = f"Purpose {i}"
            test_client.post(f"{settings.api_v1_prefix}/purposes", json=data)

        # Test pagination
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2

    def test_get_purposes_with_filters(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with filtering."""
        # Create suppliers first
        supplier_a = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier A"}
        )
        supplier_b = test_client.post(
            f"{settings.api_v1_prefix}/suppliers", json={"name": "Supplier B"}
        )
        supplier_a_id = supplier_a.json()["id"]
        supplier_b_id = supplier_b.json()["id"]

        # Create purposes with different attributes
        data1 = sample_purpose_data.copy()
        data1["status"] = "IN_PROGRESS"
        data1["supplier_id"] = supplier_a_id
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["status"] = "COMPLETED"
        data2["supplier_id"] = supplier_b_id
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test status filter
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?status=IN_PROGRESS"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "IN_PROGRESS"

        # Test supplier filter
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?supplier_id={supplier_b_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["supplier"] == "Supplier B"

    def test_get_purposes_with_search(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with search functionality."""
        # Create purposes with different descriptions
        data1 = sample_purpose_data.copy()
        data1["description"] = "Software development project"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["description"] = "Hardware procurement for buying computers"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test search in description
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=software")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "software" in data["items"][0]["description"].lower()

        # Test search in description for computers
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?search=computers"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "computers" in data["items"][0]["description"].lower()

    def test_get_purposes_with_emf_id_search(
        self, test_client: TestClient, sample_purpose_data: dict, sample_emf_data: dict
    ):
        """Test GET /purposes with emf_id search functionality."""
        # Create purpose with EMFs
        purpose_data = sample_purpose_data.copy()
        purpose_data["emfs"] = [
            sample_emf_data.copy(),
            {
                **sample_emf_data,
                "emf_id": "EMF-002",
                "costs": [{"currency": "ILS", "amount": 2000.00}],
            },
        ]

        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert create_response.status_code == 201

        # Test search by emf_id
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=EMF-001")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == create_response.json()["id"]

        # Test search by different emf_id
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=EMF-002")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == create_response.json()["id"]

        # Test search by partial emf_id
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=EMF")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == create_response.json()["id"]

        # Test search by non-existent emf_id
        response = test_client.get(f"{settings.api_v1_prefix}/purposes?search=EMF-999")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_get_purposes_with_sorting(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with sorting."""
        # Create purposes with different dates
        data1 = sample_purpose_data.copy()
        data1["expected_delivery"] = "2024-01-01"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data1)

        data2 = sample_purpose_data.copy()
        data2["expected_delivery"] = "2024-06-01"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=data2)

        # Test sort by expected_delivery ascending
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?sort_by=expected_delivery&sort_order=asc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
            data["items"][0]["expected_delivery"]
            <= data["items"][1]["expected_delivery"]
        )

        # Test sort by expected_delivery descending
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?sort_by=expected_delivery&sort_order=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert (
            data["items"][0]["expected_delivery"]
            >= data["items"][1]["expected_delivery"]
        )

    def test_get_purposes_combined_filters(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with combined filters, search, and sorting."""
        # Create multiple purposes
        for i in range(3):
            data = sample_purpose_data.copy()
            data["description"] = f"Project {i}"
            data["status"] = "IN_PROGRESS" if i % 2 == 0 else "COMPLETED"
            data["expected_delivery"] = f"2024-0{i + 1}-01"
            test_client.post(f"{settings.api_v1_prefix}/purposes", json=data)

        # Test combined filters
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?status=IN_PROGRESS&search=Project"
            f"&sort_by=expected_delivery&sort_order=desc&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # Only 'IN_PROGRESS' projects
        for item in data["items"]:
            assert item["status"] == "IN_PROGRESS"
            assert "Project" in item["description"]

    def test_get_purposes_with_hierarchy_path_filtering(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test GET /purposes with hierarchy path filtering."""
        # Create hierarchy tree: raphael -> raphael/lustig -> raphael/lustig/some
        hierarchy_raphael = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies",
            json={"type": "UNIT", "name": "raphael", "path": "raphael"},
        )
        hierarchy_lustig = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies",
            json={
                "type": "CENTER",
                "name": "lustig",
                "path": "raphael/lustig",
                "parent_id": hierarchy_raphael.json()["id"],
            },
        )
        hierarchy_some = test_client.post(
            f"{settings.api_v1_prefix}/hierarchies",
            json={
                "type": "ANAF",
                "name": "some",
                "path": "raphael/lustig/some",
                "parent_id": hierarchy_lustig.json()["id"],
            },
        )

        raphael_id = hierarchy_raphael.json()["id"]
        lustig_id = hierarchy_lustig.json()["id"]
        some_id = hierarchy_some.json()["id"]

        # Create purposes for each hierarchy level
        purpose_raphael = sample_purpose_data.copy()
        purpose_raphael["hierarchy_id"] = raphael_id
        purpose_raphael["description"] = "Purpose for raphael"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_raphael)

        purpose_lustig = sample_purpose_data.copy()
        purpose_lustig["hierarchy_id"] = lustig_id
        purpose_lustig["description"] = "Purpose for lustig"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_lustig)

        purpose_some = sample_purpose_data.copy()
        purpose_some["hierarchy_id"] = some_id
        purpose_some["description"] = "Purpose for some"
        test_client.post(f"{settings.api_v1_prefix}/purposes", json=purpose_some)

        # Test filtering by raphael hierarchy_id - should return all 3 purposes
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?hierarchy_id={raphael_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        descriptions = [item["description"] for item in data["items"]]
        assert "Purpose for raphael" in descriptions
        assert "Purpose for lustig" in descriptions
        assert "Purpose for some" in descriptions

        # Test filtering by lustig hierarchy_id - should return 2 purposes (lustig and some)
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?hierarchy_id={lustig_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        descriptions = [item["description"] for item in data["items"]]
        assert "Purpose for lustig" in descriptions
        assert "Purpose for some" in descriptions

        # Test filtering by some hierarchy_id - should return only 1 purpose (some)
        response = test_client.get(
            f"{settings.api_v1_prefix}/purposes?hierarchy_id={some_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "Purpose for some"


class TestPurposeContentAPI:
    """Test Purpose Content functionality."""

    def test_create_purpose_with_contents(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test creating a purpose with contents."""
        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["contents"]) == 1
        assert (
            data["contents"][0]["service_id"]
            == sample_purpose_data_with_contents["contents"][0]["service_id"]
        )
        assert (
            data["contents"][0]["quantity"]
            == sample_purpose_data_with_contents["contents"][0]["quantity"]
        )

    def test_create_purpose_with_invalid_service_id(
        self, test_client: TestClient, sample_purpose_data: dict
    ):
        """Test creating a purpose with invalid service_id returns 400."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [{"service_id": 999, "quantity": 2}]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 400
        assert "Service with ID 999 does not exist" in response.json()["detail"]

    def test_create_purpose_with_zero_quantity(
        self, test_client: TestClient, sample_purpose_data: dict, sample_service
    ):
        """Test creating a purpose with zero quantity returns 422."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [{"service_id": sample_service.id, "quantity": 0}]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 422

    def test_create_purpose_with_negative_quantity(
        self, test_client: TestClient, sample_purpose_data: dict, sample_service
    ):
        """Test creating a purpose with negative quantity returns 422."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [{"service_id": sample_service.id, "quantity": -1}]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        assert response.status_code == 422

    def test_create_purpose_with_duplicate_service(
        self, test_client: TestClient, sample_purpose_data: dict, sample_service
    ):
        """Test creating a purpose with duplicate service in contents fails."""
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [
            {"service_id": sample_service.id, "quantity": 2},
            {"service_id": sample_service.id, "quantity": 3},
        ]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        # This should fail due to unique constraint
        assert response.status_code == 400
        assert "already included in this purpose" in response.json()["detail"]

    def test_update_purpose_contents(
        self,
        test_client: TestClient,
        sample_purpose_data_with_contents: dict,
        sample_service,
    ):
        """Test updating purpose contents."""
        # Create purpose with contents
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        purpose_id = create_response.json()["id"]

        # Update with new contents
        update_data = {"contents": [{"service_id": sample_service.id, "quantity": 5}]}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["contents"]) == 1
        assert data["contents"][0]["quantity"] == 5

    def test_update_purpose_contents_empty(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test updating purpose with empty contents."""
        # Create purpose with contents
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        purpose_id = create_response.json()["id"]

        # Update with empty contents
        update_data = {"contents": []}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["contents"]) == 0

    def test_update_purpose_contents_invalid_service_id(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test updating purpose with invalid service_id returns 400."""
        # Create purpose with contents
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        purpose_id = create_response.json()["id"]

        # Update with invalid service_id
        update_data = {"contents": [{"service_id": 999, "quantity": 2}]}

        response = test_client.patch(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}", json=update_data
        )
        assert response.status_code == 400
        assert "Service with ID 999 does not exist" in response.json()["detail"]

    def test_cascade_delete_purpose_contents(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test that purpose contents are deleted when purpose is deleted."""
        # Create purpose with contents
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        purpose_id = create_response.json()["id"]

        # Verify purpose exists with contents
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert get_response.status_code == 200
        assert len(get_response.json()["contents"]) == 1

        # Delete purpose
        delete_response = test_client.delete(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert delete_response.status_code == 204

        # Verify purpose is deleted
        get_response = test_client.get(
            f"{settings.api_v1_prefix}/purposes/{purpose_id}"
        )
        assert get_response.status_code == 404

    def test_multiple_services_in_purpose_contents(
        self,
        test_client: TestClient,
        sample_purpose_data: dict,
        sample_service,
        sample_service_type,
    ):
        """Test creating purpose with multiple different services."""
        # Create additional service
        service2_response = test_client.post(
            f"{settings.api_v1_prefix}/services",
            json={"name": "Service 2", "service_type_id": sample_service_type.id},
        )
        service2_id = service2_response.json()["id"]

        # Create purpose with multiple services
        purpose_data = sample_purpose_data.copy()
        purpose_data["contents"] = [
            {"service_id": sample_service.id, "quantity": 2},
            {"service_id": service2_id, "quantity": 3},
        ]

        response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=purpose_data
        )
        # This should succeed with multiple different services
        assert response.status_code == 201
        data = response.json()
        assert len(data["contents"]) == 2

        # Verify both services are included
        service_ids = [content["service_id"] for content in data["contents"]]
        assert sample_service.id in service_ids
        assert service2_id in service_ids

    def test_get_purpose_with_contents_includes_service_info(
        self, test_client: TestClient, sample_purpose_data_with_contents: dict
    ):
        """Test that getting a purpose includes full content information."""
        # Create purpose with contents
        create_response = test_client.post(
            f"{settings.api_v1_prefix}/purposes", json=sample_purpose_data_with_contents
        )
        purpose_id = create_response.json()["id"]

        # Get purpose and verify contents structure
        response = test_client.get(f"{settings.api_v1_prefix}/purposes/{purpose_id}")
        assert response.status_code == 200
        data = response.json()

        assert "contents" in data
        assert len(data["contents"]) == 1
        content = data["contents"][0]
        assert "id" in content
        assert "service_id" in content
        assert "quantity" in content
        assert content["quantity"] == 2
