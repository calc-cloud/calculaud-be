"""Test utilities providing common assertion helpers and data generation functions."""

from typing import Any

from fastapi.testclient import TestClient


def assert_paginated_response(
    response_data: dict,
    expected_total: int,
    expected_page: int = 1,
    expected_limit: int = 100,
    expected_has_next: bool | None = None,
    expected_has_prev: bool | None = None,
) -> None:
    """Assert that response contains correct pagination metadata."""
    assert "items" in response_data
    assert "total" in response_data
    assert "page" in response_data
    assert "limit" in response_data
    assert "has_next" in response_data
    assert "has_prev" in response_data
    assert "pages" in response_data

    assert response_data["total"] == expected_total
    assert response_data["page"] == expected_page
    assert response_data["limit"] == expected_limit

    if expected_has_next is not None:
        assert response_data["has_next"] == expected_has_next
    if expected_has_prev is not None:
        assert response_data["has_prev"] == expected_has_prev

    # Calculate expected pages
    expected_pages = (
        (expected_total + expected_limit - 1) // expected_limit
        if expected_total > 0
        else 0
    )
    assert response_data["pages"] == expected_pages


def assert_validation_error(response, field_name: str = None) -> None:
    """Assert that response indicates validation error."""
    assert response.status_code == 422

    if field_name:
        # Check that the error mentions the specific field
        error_detail = str(response.json()).lower()
        assert field_name.lower() in error_detail


def assert_sorted_by_field(
    response_data: dict, field: str, ascending: bool = True
) -> None:
    """Assert that items are sorted by the specified field."""
    assert "items" in response_data
    items = response_data["items"]

    if len(items) <= 1:
        return  # Nothing to sort

    values = [item.get(field) for item in items]

    if ascending:
        assert values == sorted(
            values
        ), f"Items not sorted by {field} in ascending order"
    else:
        assert values == sorted(
            values, reverse=True
        ), f"Items not sorted by {field} in descending order"


def create_test_data_variations(
    base_data: dict, variations: dict[str, list]
) -> list[dict]:
    """Create multiple test data variations from base data."""
    test_data_list = []

    # Create combinations of variations
    for field, values in variations.items():
        for value in values:
            variation = base_data.copy()
            variation[field] = value
            test_data_list.append(variation)

    return test_data_list


def extract_ids(resources: list[dict]) -> list[int]:
    """Extract IDs from a list of resource dictionaries."""
    return [resource["id"] for resource in resources]


def find_resource_by_field(
    resources: list[dict], field: str, value: Any
) -> dict | None:
    """Find a resource in a list by a specific field value."""
    for resource in resources:
        if resource.get(field) == value:
            return resource
    return None


def assert_file_attachment_response(
    response_data: dict, expected_filename: str = None
) -> None:
    """Assert that file attachment response has correct structure."""
    required_fields = ["id", "original_filename", "mime_type", "file_size"]

    for field in required_fields:
        assert field in response_data, f"Missing field: {field}"

    if expected_filename:
        assert response_data["original_filename"] == expected_filename


class APITestHelper:
    """Helper class for common API testing operations."""

    def __init__(self, test_client: TestClient, base_endpoint: str):
        self.client = test_client
        self.endpoint = base_endpoint

    def create_resource(self, data: dict) -> dict:
        """Create a resource and return response data."""
        response = self.client.post(self.endpoint, json=data)
        assert response.status_code == 201
        return response.json()

    def get_resource(self, resource_id: int) -> dict:
        """Get a resource by ID and return response data."""
        response = self.client.get(f"{self.endpoint}/{resource_id}")
        assert response.status_code == 200
        return response.json()

    def update_resource(self, resource_id: int, data: dict) -> dict:
        """Update a resource and return response data."""
        response = self.client.patch(f"{self.endpoint}/{resource_id}", json=data)
        assert response.status_code == 200
        return response.json()

    def delete_resource(self, resource_id: int) -> None:
        """Delete a resource."""
        response = self.client.delete(f"{self.endpoint}/{resource_id}")
        assert response.status_code == 204

    def list_resources(self, **params) -> dict:
        """List resources with optional query parameters."""
        response = self.client.get(self.endpoint, params=params)
        assert response.status_code == 200
        return response.json()

    def search_resources(self, search_term: str, **params) -> dict:
        """Search resources by term."""
        params["search"] = search_term
        return self.list_resources(**params)
