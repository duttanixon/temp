"""
Test cases for customer solution management routes.
"""
import pytest
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, Customer, CustomerSolution, LicenseStatus, User, Solution
from app.core.config import settings


# Test cases for getting customer solutions (GET /customer-solutions)
def test_get_customer_solutions_admin(client: TestClient, admin_token: str, db: Session):
    """Test admin getting all customer solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # We created at least one customer solution in our seed data
    
    # Check structure of returned customer solutions
    customer_solution = data[0]
    assert "id" in customer_solution
    assert "customer_id" in customer_solution
    assert "solution_id" in customer_solution
    assert "license_status" in customer_solution
    assert "max_devices" in customer_solution


def test_get_customer_solutions_engineer(client: TestClient, engineer_token: str):
    """Test engineer getting all customer solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_customer_solutions_for_specific_customer(client: TestClient, admin_token: str, customer: Customer):
    """Test getting customer solutions for a specific customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions?customer_id={customer.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned customer solutions should belong to the specified customer
    for cs in data:
        assert str(cs["customer_id"]) == str(customer.customer_id)


def test_get_customer_solutions_customer_admin(client: TestClient, customer_admin_token: str, customer_admin_user: User, customer: Customer):
    """Test customer admin getting customer solutions for their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned customer solutions should belong to the customer admin's customer
    for cs in data:
        assert str(cs["customer_id"]) == str(customer_admin_user.customer_id)


def test_get_customer_solutions_customer_user(client: TestClient, customer_user_token: str, customer_user: User):
    """Test customer user getting customer solutions for their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response
    assert response.status_code == 403

def test_get_customer_solutions_customer_admin_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: Customer):
    """Test customer admin attempting to get customer solutions for a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions?customer_id={suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403

# # Test cases for creating customer solutions (POST /customer-solutions)
# def test_create_customer_solution_admin(client: TestClient, db: Session, admin_token: str, customer: Customer, db: Session):
#     """Test admin creating a new customer solution"""
#     # Get a solution that doesn't yet have a customer solution for our customer
#     solution = db.query(Solution).filter(Solution.name == "Beta Solution").first()
    
#     customer_solution_data = {
#         "customer_id": str(customer.customer_id),
#         "solution_id": str(solution.solution_id),
#         "license_status": "ACTIVE",
#         "max_devices": 5,
#         "expiration_date": (date.today() + timedelta(days=365)).isoformat(),  # One year from now
#         "configuration_template": {"param1": "custom1", "param2": "custom2"}
#     }
    
#     response = client.post(
#         f"{settings.API_V1_STR}/customer-solutions",
#         headers={"Authorization": f"Bearer {admin_token}"},
#         json=customer_solution_data
#     )
    
#     # Check response
#     assert response.status_code == 200
#     data = response.json()
#     assert str(data["customer_id"]) == customer_solution_data["customer_id"]
#     assert str(data["solution_id"]) == customer_solution_data["solution_id"]
#     assert data["max_devices"] == customer_solution_data["max_devices"]
#     assert "id" in data
    
#     # Verify customer solution was created in database
#     db.expire_all()
#     created_cs = db.query(CustomerSolution).filter(
#         CustomerSolution.customer_id == customer.customer_id,
#         CustomerSolution.solution_id == solution.solution_id
#     ).first()
#     assert created_cs is not None
#     assert created_cs.max_devices == customer_solution_data["max_devices"]
    
#     # Verify audit log
#     audit_log = db.query(AuditLog).filter(
#         AuditLog.action_type == "CUSTOMER_SOLUTION_CREATE",
#         AuditLog.resource_id == str(created_cs.id)
#     ).first()
#     assert audit_log is not None


def test_create_customer_solution_already_exists(client: TestClient, db: Session, admin_token: str, customer: Customer):
    """Test creating a customer solution that already exists"""
    # Get an existing customer solution
    existing_cs = db.query(CustomerSolution).filter(
        CustomerSolution.customer_id == customer.customer_id
    ).first()
    
    customer_solution_data = {
        "customer_id": str(existing_cs.customer_id),
        "solution_id": str(existing_cs.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 10
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Customer already has access to solution Test Solution" in data["detail"]


def test_create_customer_solution_nonexistent_customer(client: TestClient, admin_token: str, db: Session):
    """Test creating a customer solution with non-existent customer"""
    # Get a valid solution id
    solution = db.query(Solution).first()
    nonexistent_id = uuid.uuid4()
    
    customer_solution_data = {
        "customer_id": str(nonexistent_id),
        "solution_id": str(solution.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer not found" in data["detail"]


def test_create_customer_solution_nonexistent_solution(client: TestClient, admin_token: str, customer: Customer):
    """Test creating a customer solution with non-existent solution"""
    nonexistent_id = uuid.uuid4()
    
    customer_solution_data = {
        "customer_id": str(customer.customer_id),
        "solution_id": str(nonexistent_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Solution not found" in data["detail"]


def test_create_customer_solution_non_admin(client: TestClient, customer_user_token: str, db: Session, customer: Customer):
    """Test non-admin attempting to create a customer solution"""
    # Get a solution
    solution = db.query(Solution).first()
    
    customer_solution_data = {
        "customer_id": str(customer.customer_id),
        "solution_id": str(solution.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=customer_solution_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


# Test cases for getting customer solution by ID (GET /customer-solutions/{id})
def test_get_customer_solution_by_id_admin(client: TestClient, admin_token: str, db: Session):
    """Test admin getting a specific customer solution by ID"""
    # Get a customer solution ID from database
    cs = db.query(CustomerSolution).first()
    
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()[0]
    assert str(data["id"]) == str(cs.id)
    assert str(data["customer_id"]) == str(cs.customer_id)
    assert str(data["solution_id"]) == str(cs.solution_id)
    assert "solution_name" in data  # Should include the solution name


def test_get_customer_solution_by_id_customer_admin_own_customer(client: TestClient, customer_admin_token: str, 
                                                             customer_admin_user: User, db: Session):
    """Test customer admin getting a customer solution for their customer"""
    # Get a customer solution for the customer admin's customer
    cs = db.query(CustomerSolution).filter(
        CustomerSolution.customer_id == customer_admin_user.customer_id
    ).first()
    
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()[0]
    assert str(data["id"]) == str(cs.id)
    assert str(data["customer_id"]) == str(customer_admin_user.customer_id)


def test_get_customer_solution_by_id_customer_admin_different_customer(
    client: TestClient, 
    customer_admin_token: str,
    suspended_customer_solution: CustomerSolution
):
    """Test customer admin attempting to get customer solution for different customer"""
    # Try to get it as customer admin
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/customer/{suspended_customer_solution.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]

def test_get_customer_solution_nonexistent_id(client: TestClient, admin_token: str):
    """Test getting customer solution with non-existent ID"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Not Found" in data["detail"]

# Test cases for updating customer solution (PUT /customer-solutions/{id})
def test_update_customer_solution_admin(client: TestClient, db: Session, admin_token: str):
    """Test admin updating a customer solution"""
    # Get a customer solution ID from database
    cs = db.query(CustomerSolution).first()
    
    update_data = {
        "max_devices": 20,
        "license_status": "SUSPENDED",
        "expiration_date": (date.today() + timedelta(days=180)).isoformat()  # 6 months from now
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["max_devices"] == update_data["max_devices"]
    assert data["license_status"] == update_data["license_status"]
    
    # Verify database updates
    db.expire_all()
    updated_cs = db.query(CustomerSolution).filter(CustomerSolution.id == cs.id).first()
    assert updated_cs.max_devices == update_data["max_devices"]
    assert updated_cs.license_status == LicenseStatus.SUSPENDED
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_UPDATE",
        AuditLog.resource_id == str(cs.id)
    ).first()
    assert audit_log is not None

def test_update_customer_solution_non_admin(client: TestClient, customer_user_token: str, db: Session):
    """Test non-admin attempting to update a customer solution"""
    # Get a customer solution ID from database
    cs = db.query(CustomerSolution).first()
    
    update_data = {
        "max_devices": 30
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


def test_update_customer_solution_nonexistent_id(client: TestClient, admin_token: str):
    """Test updating a non-existent customer solution"""
    nonexistent_id = uuid.uuid4()
    
    update_data = {
        "max_devices": 15
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{nonexistent_id}/solution/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer solution not found" in data["detail"]

# Test cases for suspending customer solution (POST /customer-solutions/{id}/suspend)
def test_suspend_customer_solution(client: TestClient, db: Session, admin_token: str):
    """Test suspending a customer solution"""
    # Get an active customer solution
    cs = db.query(CustomerSolution).filter(
        CustomerSolution.license_status == LicenseStatus.ACTIVE
    ).first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["license_status"] == "SUSPENDED"
    
    # Verify database update
    db.expire_all()
    suspended_cs = db.query(CustomerSolution).filter(CustomerSolution.id == cs.id).first()
    assert suspended_cs.license_status == LicenseStatus.SUSPENDED
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_SUSPEND",
        AuditLog.resource_id == str(cs.id)
    ).first()
    assert audit_log is not None


def test_suspend_customer_solution_non_admin(client: TestClient, customer_user_token: str, db: Session):
    """Test non-admin attempting to suspend a customer solution"""
    # Get a customer solution ID from database
    cs = db.query(CustomerSolution).first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for activating customer solution (POST /customer-solutions/{id}/activate)
def test_activate_customer_solution(client: TestClient, db: Session, admin_token: str):
    """Test activating a suspended customer solution"""
    # First suspend a customer solution
    cs = db.query(CustomerSolution).filter(
        CustomerSolution.license_status == LicenseStatus.ACTIVE
    ).first()
    
    # Use the API to suspend it
    suspend_response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert suspend_response.status_code == 200
    
    # Now try to activate it
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["license_status"] == "ACTIVE"
    
    # Verify database update
    db.expire_all()
    activated_cs = db.query(CustomerSolution).filter(CustomerSolution.id == cs.id).first()
    assert activated_cs.license_status == LicenseStatus.ACTIVE
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_ACTIVATE",
        AuditLog.resource_id == str(cs.id)
    ).first()
    assert audit_log is not None


def test_activate_customer_solution_non_admin(client: TestClient, customer_user_token: str, db: Session):
    """Test non-admin attempting to activate a customer solution"""
    # Get a customer solution ID from database
    cs = db.query(CustomerSolution).first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/activate",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]