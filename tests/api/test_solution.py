"""
Test cases for solution management routes.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DeviceType, AuditLog, Solution, SolutionStatus, User, Device, Customer
from app.core.config import settings

# Test cases for solution listing (GET /solutions)
def test_get_all_solutions_admin(client: TestClient, admin_token: str):
    """Test admin getting all solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # We created at least 2 test solutions in our seed data
    
    # Check structure of returned solutions
    solution = data[0]
    assert "solution_id" in solution
    assert "name" in solution
    assert "compatibility" in solution
    assert "version" in solution

def test_get_all_solutions_engineer(client: TestClient, engineer_token: str):
    """Test engineer getting all solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_solutions_customer_user(client: TestClient, customer_admin_token: str, customer_admin_user2: User):
    """Test customer user getting solutions assigned to their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should at least get the Test Solution which is assigned to the active customer
    assert len(data) >= 1

def test_get_solutions_filter_by_device_type(client: TestClient, admin_token: str):
    """Test getting solutions filtered by device type"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions?device_type=NVIDIA_JETSON",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = response.json()
    # Check response
    assert response.status_code == 200

    assert isinstance(data, list)
    
    # Verify all returned solutions are compatible with the device type
    for solution in data:
        assert DeviceType.NVIDIA_JETSON in solution["compatibility"]


def test_get_solutions_filter_active_only(client: TestClient, admin_token: str):
    """Test getting only active solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions?active_only=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify all returned solutions have active status
    for solution in data:
        assert solution["status"] == "ACTIVE"

def test_get_solutions_invalid_device_type(client: TestClient, admin_token: str):
    """Test filtering with invalid device type"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions?device_type=INVALID_TYPE",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should fail validation
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid device type" in data["detail"]


# Test cases for admin view solutions listing (GET /solutions/admin)
def test_get_solutions_admin_view(client: TestClient, admin_token: str):
    """Test getting solutions with admin view (includes customer counts)"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions/admin",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Check admin view contains extended fields
    solution = data[0]
    assert "solution_id" in solution
    assert "name" in solution
    assert "customers_count" in solution

def test_get_solutions_admin_view_no_permission(client: TestClient, customer_admin_token: str):
    """Test customer user attempting to access admin view"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions/admin",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for available solutions endpoint (GET /solutions/available)
def test_get_available_solutions(client: TestClient, customer_admin_token: str, customer_admin_user: User):
    """Test getting available solutions for the customer"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions/available",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Should only include active solutions assigned to the customer
    for solution in data:
        assert solution["status"] == "ACTIVE"

def test_get_available_solutions_with_device_type(client: TestClient, customer_admin_token: str):
    """Test getting available solutions filtered by device type"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions/available?device_type=NVIDIA_JETSON",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify all returned solutions are compatible with the device type
    for solution in data:
        assert DeviceType.NVIDIA_JETSON in solution["compatibility"]
        assert solution["status"] == "ACTIVE"

# Test cases for solution creation (POST /solutions)
def test_create_solution_admin(client: TestClient, db: Session, admin_token: str):
    """Test admin creating a new solution"""
    solution_data = {
        "name": "New Test Solution",
        "description": "A new test solution for testing",
        "version": "1.0.0",
        "compatibility": ["NVIDIA_JETSON", "RASPBERRY_PI"],
        "status": "ACTIVE",
        "configuration_template": {"param1": "default1", "param2": "default2"}
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == solution_data["name"]
    assert data["version"] == solution_data["version"]
    assert "solution_id" in data
    
    # Verify solution was created in database
    db.expire_all()
    created_solution = db.query(Solution).filter(Solution.name == solution_data["name"]).first()
    assert created_solution is not None
    assert created_solution.version == solution_data["version"]
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "SOLUTION_CREATE",
        AuditLog.resource_id == str(created_solution.solution_id)
    ).first()
    assert audit_log is not None

def test_create_solution_existing_name(client: TestClient, admin_token: str, db: Session):
    """Test creating solution with existing name"""
    # Get existing solution
    existing_solution = db.query(Solution).first()
    
    solution_data = {
        "name": existing_solution.name,  # Already exists
        "description": "A duplicate solution",
        "version": "1.0.0",
        "compatibility": ["NVIDIA_JETSON"],
        "status": "ACTIVE"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"]



def test_create_solution_invalid_device_type(client: TestClient, admin_token: str):
    """Test creating solution with invalid device type"""
    solution_data = {
        "name": "Invalid Device Type Solution",
        "description": "A solution with invalid device type",
        "version": "1.0.0",
        "compatibility": ["INVALID_DEVICE_TYPE"],
        "status": "ACTIVE"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should fail with 422 Unprocessable Entity
    # This is FastAPI's standard response code for validation errors
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Validation error should be related to the compatibility field
    validation_errors = data["detail"]
    assert any("compatibility" in str(error).lower() for error in validation_errors)

def test_create_solution_non_admin(client: TestClient, customer_admin_token: str):
    """Test non-admin attempting to create solution"""
    solution_data = {
        "name": "Unauthorized Solution",
        "description": "A solution from unauthorized user",
        "version": "1.0.0",
        "compatibility": ["NVIDIA_JETSON"],
        "status": "ACTIVE"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=solution_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for getting solution by ID (GET /solutions/{solution_id})
def test_get_solution_by_id_admin(client: TestClient, admin_token: str, db: Session):
    """Test admin getting a specific solution by ID"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    response = client.get(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["solution_id"]) == str(solution.solution_id)
    assert data["name"] == solution.name
    assert "customers_count" in data  # Admin gets count info

def test_get_solution_by_id_customer_user_with_access(client: TestClient, customer_admin_token: str, db: Session):
    """Test customer user getting a solution assigned to their customer"""
    # Get a solution ID from database that is assigned to the customer
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    response = client.get(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["solution_id"]) == str(solution.solution_id)
    assert data["name"] == solution.name
    assert "customers_count" not in data  # Regular users don't get admin info


def test_get_solution_by_id_customer_user_no_access(client: TestClient, customer_admin_token: str, db: Session):
    """Test customer user attempting to get a solution not assigned to their customer"""
    # Get a solution ID from database that is not assigned to the customer
    solution = db.query(Solution).filter(Solution.name == "Beta Solution").first()
    
    response = client.get(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]

def test_get_solution_nonexistent_id(client: TestClient, admin_token: str):
    """Test getting solution with non-existent ID"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/solutions/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

# Test cases for updating solution (PUT /solutions/{solution_id})
def test_update_solution_admin(client: TestClient, db: Session, admin_token: str):
    """Test admin updating a solution"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    update_data = {
        "name": "Updated Test Solution",
        "description": "An updated test solution",
        "version": "1.1.0"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["version"] == update_data["version"]
    
    # Verify database updates
    db.expire_all()
    updated_solution = db.query(Solution).filter(Solution.solution_id == solution.solution_id).first()
    assert updated_solution.name == update_data["name"]
    assert updated_solution.version == update_data["version"]
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "SOLUTION_UPDATE",
        AuditLog.resource_id == str(solution.solution_id)
    ).first()
    assert audit_log is not None

def test_update_solution_compatibility(client: TestClient, db: Session, admin_token: str):
    """Test updating solution compatibility"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    update_data = {
        "compatibility": ["NVIDIA_JETSON"]  # Change to only support Jetson
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["compatibility"]) == 1
    assert "NVIDIA_JETSON" in data["compatibility"]
    
    # Verify database updates
    db.expire_all()
    updated_solution = db.query(Solution).filter(Solution.solution_id == solution.solution_id).first()
    assert len(updated_solution.compatibility) == 1
    assert "NVIDIA_JETSON" in updated_solution.compatibility


def test_update_solution_invalid_compatibility(client: TestClient, admin_token: str, db: Session):
    """Test updating solution with invalid device compatibility"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    update_data = {
        "compatibility": ["INVALID_DEVICE"]
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should fail validation
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid device type" in data["detail"]


def test_update_solution_new_name_conflict(client: TestClient, admin_token: str, db: Session):
    """Test updating solution with a name that already exists for another solution"""
    # Get two different solutions
    solution1 = db.query(Solution).filter(Solution.name == "Test Solution").first()
    solution2 = db.query(Solution).filter(Solution.name == "Beta Solution").first()
    
    update_data = {
        "name": solution2.name  # Try to use the name of solution2
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solutions/{solution1.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"]


def test_update_solution_non_admin(client: TestClient, customer_admin_token: str, db: Session):
    """Test non-admin attempting to update solution"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    update_data = {
        "description": "Unauthorized update"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


# Test cases for deprecating solution (POST /solutions/{solution_id}/deprecate)
def test_deprecate_solution(client: TestClient, db: Session, admin_token: str):
    """Test deprecating a solution"""
    # Get an active solution
    solution = db.query(Solution).filter(Solution.status == SolutionStatus.ACTIVE).first()
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}/deprecate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DEPRECATED"
    
    # Verify database update
    db.expire_all()
    deprecated_solution = db.query(Solution).filter(Solution.solution_id == solution.solution_id).first()
    assert deprecated_solution.status == SolutionStatus.DEPRECATED
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "SOLUTION_DEPRECATE",
        AuditLog.resource_id == str(solution.solution_id)
    ).first()
    assert audit_log is not None


def test_deprecate_solution_non_admin(client: TestClient, customer_admin_token: str, db: Session):
    """Test non-admin attempting to deprecate a solution"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Test Solution").first()
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}/deprecate",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for activating solution (POST /solutions/{solution_id}/activate)
def test_activate_solution(client: TestClient, db: Session, admin_token: str):
    """Test activating a deprecated solution"""
    # First deprecate a solution
    solution = db.query(Solution).filter(Solution.status == SolutionStatus.ACTIVE).first()
    
    # Use the API to deprecate it
    response = client.post(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}/deprecate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Now try to activate it
    response = client.post(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    
    # Verify database update
    db.expire_all()
    activated_solution = db.query(Solution).filter(Solution.solution_id == solution.solution_id).first()
    assert activated_solution.status == SolutionStatus.ACTIVE
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "SOLUTION_ACTIVATE",
        AuditLog.resource_id == str(solution.solution_id)
    ).first()
    assert audit_log is not None


def test_activate_solution_non_admin(client: TestClient, customer_admin_token: str, db: Session):
    """Test non-admin attempting to activate a solution"""
    # Get a solution ID from database
    solution = db.query(Solution).filter(Solution.name == "Beta Solution").first()
    
    response = client.post(
        f"{settings.API_V1_STR}/solutions/{solution.solution_id}/activate",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for compatible solutions for device (GET /solutions/compatibility/device/{device_id})
def test_get_compatible_solutions_for_device_admin(client: TestClient, admin_token: str, device: Device):
    """Test admin getting compatible solutions for a device"""
    response = client.get(
        f"{settings.API_V1_STR}/solutions/compatibility/device/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify returned solutions are compatible with the device type
    for solution in data:
        assert device.device_type.value in solution["compatibility"]


def test_get_compatible_solutions_for_device_customer_user(client: TestClient, customer_admin_token: str, 
                                                          device: Device, db: Session):
    """Test customer user getting compatible solutions for their device"""

    ## todo - Should customer user be able to go through this endpoint??
    response = client.get(
        f"{settings.API_V1_STR}/solutions/compatibility/device/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify returned solutions are compatible with the device type and available to the customer
    for solution in data:
        assert device.device_type.value in solution["compatibility"]
        assert solution["status"] == "ACTIVE"

def test_get_compatible_solutions_for_nonexistent_device(client: TestClient, admin_token: str):
    """Test getting compatible solutions for a non-existent device"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/solutions/compatibility/device/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

def test_get_compatible_solutions_for_device_different_customer(client: TestClient, customer_admin_token: str,
                                                               suspended_customer: Customer, admin_token: str,
                                                               db: Session):
    """Test customer user attempting to get compatible solutions for a device of different customer"""
    # Create a device for the suspended customer
    device_data = {
        "description": "A device for different customer",
        "mac_address": "AA:BB:CC:99:88:77",
        "serial_number": "SNDIFFERENT",
        "device_type": "NVIDIA_JETSON",
        "customer_id": str(suspended_customer.customer_id)
    }
    
    create_response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    
    created_device = create_response.json()
    
    # Try to get compatible solutions as customer user
    response = client.get(
        f"{settings.API_V1_STR}/solutions/compatibility/device/{created_device['device_id']}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]