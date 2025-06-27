"""Base test classes providing common test patterns for API testing."""

from typing import Any

from fastapi.testclient import TestClient


class CRUDTestMixin:
    """Mixin providing standard CRUD test methods for API resources."""

    # These attributes should be set by subclasses
    resource_name: str = None  # e.g., "suppliers"
    resource_endpoint: str = None  # e.g., "/api/v1/suppliers"
    create_data_fixture: str = None  # e.g., "sample_supplier_data"
    instance_fixture: str = None  # e.g., "sample_supplier"

    def test_get_empty_list(self, test_client: TestClient):
        """Test GET /{resource} returns empty list initially."""
        response = test_client.get(self.resource_endpoint)
        assert response.status_code == 200
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 100,
            "has_next": False,
            "has_prev": False,
            "pages": 0,
        }

    def test_create_resource(self, test_client: TestClient, request):
        """Test POST /{resource} creates new resource."""
        create_data = request.getfixturevalue(self.create_data_fixture)
        response = test_client.post(self.resource_endpoint, json=create_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        # Verify created data matches input
        for key, value in create_data.items():
            if key in data:
                assert data[key] == value

    def test_get_resource_by_id(self, test_client: TestClient, request):
        """Test GET /{resource}/{id} returns resource."""
        instance = request.getfixturevalue(self.instance_fixture)
        response = test_client.get(f"{self.resource_endpoint}/{instance.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance.id

    def test_get_resource_not_found(self, test_client: TestClient):
        """Test GET /{resource}/{id} returns 404 for non-existent resource."""
        response = test_client.get(f"{self.resource_endpoint}/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_patch_resource(self, test_client: TestClient, request):
        """Test PATCH /{resource}/{id} updates resource."""
        instance = request.getfixturevalue(self.instance_fixture)
        update_data = self._get_update_data()
        response = test_client.patch(
            f"{self.resource_endpoint}/{instance.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance.id
        # Verify updated data
        for key, value in update_data.items():
            if key in data:
                assert data[key] == value

    def test_patch_resource_not_found(self, test_client: TestClient):
        """Test PATCH /{resource}/{id} returns 404 for non-existent resource."""
        update_data = self._get_update_data()
        response = test_client.patch(
            f"{self.resource_endpoint}/999999", json=update_data
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_resource(self, test_client: TestClient, request):
        """Test DELETE /{resource}/{id} deletes resource."""
        instance = request.getfixturevalue(self.instance_fixture)
        response = test_client.delete(f"{self.resource_endpoint}/{instance.id}")
        assert response.status_code == 204

        # Verify resource is deleted
        get_response = test_client.get(f"{self.resource_endpoint}/{instance.id}")
        assert get_response.status_code == 404

    def test_delete_resource_not_found(self, test_client: TestClient):
        """Test DELETE /{resource}/{id} returns 404 for non-existent resource."""
        response = test_client.delete(f"{self.resource_endpoint}/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def _get_update_data(self) -> dict[str, Any]:
        """Get data for update operations. Should be overridden by subclasses."""
        return {"name": "Updated Name"}


class PaginationTestMixin:
    """Mixin providing pagination test methods for API resources."""

    # These attributes should be set by subclasses
    resource_endpoint: str = None
    multiple_instances_fixture: str = None  # e.g., "multiple_suppliers"

    def test_pagination_first_page(self, test_client: TestClient, request):
        """Test pagination on first page."""
        instances = request.getfixturevalue(self.multiple_instances_fixture)
        total_count = len(instances)

        response = test_client.get(f"{self.resource_endpoint}?page=1&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == min(3, total_count)
        assert data["total"] == total_count
        assert data["page"] == 1
        assert data["limit"] == 3
        assert data["has_prev"] is False
        assert data["has_next"] == (total_count > 3)

    def test_pagination_middle_page(self, test_client: TestClient, request):
        """Test pagination on middle page."""
        instances = request.getfixturevalue(self.multiple_instances_fixture)
        total_count = len(instances)

        if total_count <= 3:
            # Skip test if not enough data for middle page
            return

        response = test_client.get(f"{self.resource_endpoint}?page=2&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == min(3, total_count - 3)
        assert data["page"] == 2
        assert data["has_prev"] is True
        assert data["has_next"] == (total_count > 6)

    def test_pagination_last_page(self, test_client: TestClient, request):
        """Test pagination on last page."""
        instances = request.getfixturevalue(self.multiple_instances_fixture)
        total_count = len(instances)

        if total_count <= 3:
            # Skip test if not enough data for multiple pages
            return

        last_page = (total_count + 2) // 3  # Ceiling division for page count
        response = test_client.get(f"{self.resource_endpoint}?page={last_page}&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == last_page
        assert data["has_next"] is False
        assert data["has_prev"] is True


class SearchTestMixin:
    """Mixin providing search test methods for API resources."""

    # These attributes should be set by subclasses
    resource_endpoint: str = None
    search_instances_fixture: str = None  # e.g., "search_suppliers"
    search_field: str = "name"  # Field to search in

    def test_search_case_insensitive(self, test_client: TestClient, request):
        """Test that search is case-insensitive."""
        instances = request.getfixturevalue(self.search_instances_fixture)

        # Find a search term that should return results
        search_term = self._get_search_term(instances, "tech")
        if not search_term:
            return  # Skip if no suitable search term found

        # Test uppercase search
        response = test_client.get(
            f"{self.resource_endpoint}?search={search_term.upper()}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

        # Verify all results contain the search term
        for item in data["items"]:
            field_value = item.get(self.search_field, "").lower()
            assert search_term.lower() in field_value

    def test_search_partial_match(self, test_client: TestClient, request):
        """Test that search works with partial matches."""
        instances = request.getfixturevalue(self.search_instances_fixture)

        # Find a partial search term
        search_term = self._get_search_term(instances, "corp")
        if not search_term:
            return  # Skip if no suitable search term found

        response = test_client.get(f"{self.resource_endpoint}?search={search_term}")
        assert response.status_code == 200
        data = response.json()

        # Verify all results contain the search term
        for item in data["items"]:
            field_value = item.get(self.search_field, "").lower()
            assert search_term.lower() in field_value

    def test_search_no_results(self, test_client: TestClient, request):
        """Test search with no matching results."""
        response = test_client.get(
            f"{self.resource_endpoint}?search=nonexistentterm12345"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_search_with_pagination(self, test_client: TestClient, request):
        """Test search combined with pagination."""
        instances = request.getfixturevalue(self.search_instances_fixture)

        # Find a search term that returns multiple results
        search_term = self._get_common_search_term(instances)
        if not search_term:
            return  # Skip if no suitable search term found

        response = test_client.get(
            f"{self.resource_endpoint}?search={search_term}&page=1&limit=2"
        )
        assert response.status_code == 200
        data = response.json()

        if data["total"] > 2:
            assert len(data["items"]) == 2
            assert data["has_next"] is True
        assert data["page"] == 1

    def _get_search_term(self, instances, preferred_term: str) -> str | None:
        """Find a search term that exists in the test data."""
        for instance in instances:
            field_value = getattr(instance, self.search_field, "").lower()
            if preferred_term in field_value:
                return preferred_term
        return None

    def _get_common_search_term(self, instances) -> str | None:
        """Find a search term that appears in multiple instances."""
        # Common terms to look for
        common_terms = ["tech", "corp", "inc", "ltd", "solutions", "services"]

        for term in common_terms:
            count = sum(
                1
                for instance in instances
                if term in getattr(instance, self.search_field, "").lower()
            )
            if count >= 2:  # Return term that appears in at least 2 instances
                return term
        return None


class BaseAPITestClass(CRUDTestMixin, PaginationTestMixin, SearchTestMixin):
    """Base test class combining all mixins for complete API testing."""

    # Subclasses should set these attributes
    resource_name: str = None
    resource_endpoint: str = None
    create_data_fixture: str = None
    instance_fixture: str = None
    multiple_instances_fixture: str = None
    search_instances_fixture: str = None
    search_field: str = "name"
