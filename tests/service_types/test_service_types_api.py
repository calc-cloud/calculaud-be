import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.service_types.schemas import ServiceTypeCreate, ServiceTypeUpdate


def test_create_service_type(client: TestClient, db: Session):
    """Test creating a new service type."""
    service_type_data = {"name": "Software Development"}
    response = client.post("/api/v1/service-types/", json=service_type_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == service_type_data["name"]
    assert "id" in data


def test_get_service_types_paginated(client: TestClient, db: Session):
    """Test getting service types with pagination."""
    # Create some test data
    service_types = [
        {"name": "Software Development"},
        {"name": "Hardware Procurement"},
        {"name": "Consulting Services"},
    ]
    
    for st in service_types:
        client.post("/api/v1/service-types/", json=st)
    
    response = client.get("/api/v1/service-types/?page=1&limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["limit"] == 2


def test_get_service_type_by_id(client: TestClient, db: Session):
    """Test getting a specific service type by ID."""
    # Create a service type
    create_response = client.post(
        "/api/v1/service-types/", json={"name": "Test Service Type"}
    )
    service_type_id = create_response.json()["id"]
    
    # Get the service type
    response = client.get(f"/api/v1/service-types/{service_type_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == service_type_id
    assert data["name"] == "Test Service Type"


def test_patch_service_type(client: TestClient, db: Session):
    """Test patching a service type."""
    # Create a service type
    create_response = client.post(
        "/api/v1/service-types/", json={"name": "Original Name"}
    )
    service_type_id = create_response.json()["id"]
    
    # Patch the service type
    patch_data = {"name": "Updated Name"}
    response = client.patch(f"/api/v1/service-types/{service_type_id}", json=patch_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"


def test_delete_service_type(client: TestClient, db: Session):
    """Test deleting a service type."""
    # Create a service type
    create_response = client.post(
        "/api/v1/service-types/", json={"name": "To Delete"}
    )
    service_type_id = create_response.json()["id"]
    
    # Delete the service type
    response = client.delete(f"/api/v1/service-types/{service_type_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/service-types/{service_type_id}")
    assert get_response.status_code == 404


def test_get_nonexistent_service_type(client: TestClient, db: Session):
    """Test getting a service type that doesn't exist."""
    response = client.get("/api/v1/service-types/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Service type not found"


def test_create_duplicate_service_type(client: TestClient, db: Session):
    """Test creating a service type with duplicate name."""
    service_type_data = {"name": "Duplicate Service"}
    
    # Create first service type
    response1 = client.post("/api/v1/service-types/", json=service_type_data)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post("/api/v1/service-types/", json=service_type_data)
    assert response2.status_code == 400  # Should fail due to unique constraint


def test_patch_nonexistent_service_type(client: TestClient, db: Session):
    """Test patching a service type that doesn't exist."""
    patch_data = {"name": "Updated Name"}
    response = client.patch("/api/v1/service-types/999", json=patch_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Service type not found"


def test_delete_nonexistent_service_type(client: TestClient, db: Session):
    """Test deleting a service type that doesn't exist."""
    response = client.delete("/api/v1/service-types/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Service type not found"


def test_service_type_validation(client: TestClient, db: Session):
    """Test service type validation."""
    # Test empty name
    response = client.post("/api/v1/service-types/", json={"name": ""})
    assert response.status_code == 422
    
    # Test name too long
    long_name = "a" * 101
    response = client.post("/api/v1/service-types/", json={"name": long_name})
    assert response.status_code == 422 