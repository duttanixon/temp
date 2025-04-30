"""
Test cases for customer management routes
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.audit_log import AuditLog
from app.models.customer import Customer, CustomerStatus
from app.core.config import settings

# Test cases for customer listing (GET /customers)
def test_get_all_customers_admin(client: TestClient, admin_token: str):
    """Test admin getting all customers"""
    response = client.get(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # We created 2 test customers in our seed data

def test_get_all_customers_non_admin(client: TestClient, customer_user_token: str):
    """Test non-admin attempting to get all customers"""
    response = client.get(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

def test_get_all_customers_pagination(client: TestClient, admin_token: str):
    """Test pagination for customers listing"""
    response = client.get(
        f"{settings.API_V1_STR}/customers?skip=1&limit=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # We requested just 1 item

# Test cases for customer creation (POST /customers)
@patch('app.utils.aws_iot.iot_core.create_customer_thing_group')
def test_create_customer_admin(mock_create_thing_group, client: TestClient, db: Session, admin_token: str):
    """Test admin creating a new customer"""
    # Configure mock to return a suitable response
    mock_create_thing_group.return_value = {
        "thing_group_name": "customer-test",
        "thing_group_arn": "arn:aws:iot:region:account:thinggroup/customer-test"
    }
    
    customer_data = {
        "name": "New Test Customer",
        "contact_email": "contact@newtestcustomer.com",
        "address": "123 New Test Street"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert data["contact_email"] == customer_data["contact_email"]
    assert "customer_id" in data
    
    # Verify customer was created in database
    db.expire_all()
    created_customer = db.query(Customer).filter(Customer.name == customer_data["name"]).first()
    assert created_customer is not None
    assert created_customer.status == CustomerStatus.ACTIVE
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_CREATE",
        AuditLog.resource_id == str(created_customer.customer_id)
    ).first()
    assert audit_log is not None

def test_create_customer_existing_name(client: TestClient, admin_token: str, customer: Customer):
    """Test creating customer with existing name"""
    customer_data = {
        "name": customer.name,  # Already exists
        "contact_email": "contact@duplicate.com",
        "address": "123 Duplicate Street"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"]

def test_create_customer_invalid_email(client: TestClient, admin_token: str):
    """Test creating customer with invalid email format"""
    customer_data = {
        "name": "Invalid Email Customer",
        "contact_email": "not-an-email",
        "address": "123 Invalid Street"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_data
    )
    
    # Check response - should fail validation
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_create_customer_non_admin(client: TestClient, customer_user_token: str):
    """Test non-admin attempting to create customer"""
    customer_data = {
        "name": "Unauthorized Customer",
        "contact_email": "contact@unauthorized.com",
        "address": "123 Unauthorized Street"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customers",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=customer_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


# Test cases for getting customer by ID (GET /customers/{customer_id})
def test_get_customer_by_id_admin(client: TestClient, admin_token: str, customer: Customer):
    """Test admin getting customer by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["customer_id"]) == str(customer.customer_id)
    assert data["name"] == customer.name
    assert data["contact_email"] == customer.contact_email

def test_get_customer_by_id_engineer(client: TestClient, engineer_token: str, customer: Customer):
    """Test engineer getting customer by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    
    # Check response - engineers should have access
    assert response.status_code == 200
    data = response.json()
    assert str(data["customer_id"]) == str(customer.customer_id)

def test_get_customer_by_id_non_admin(client: TestClient, customer_user_token: str, customer: Customer):
    """Test non-admin/non-engineer attempting to get customer by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

def test_get_customer_nonexistent_id(client: TestClient, admin_token: str):
    """Test getting customer with non-existent ID"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/customers/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

# Test cases for updating customer (PUT /customers/{customer_id})
def test_update_customer_admin(client: TestClient, db: Session, admin_token: str, customer: Customer):
    """Test admin updating a customer"""
    update_data = {
        "name": "Updated Customer Name",
        "contact_email": "updated@customer.com",
        "address": "456 Updated Street"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["contact_email"] == update_data["contact_email"]
    
    # Verify database updates
    db.expire_all()
    updated_customer = db.query(Customer).filter(Customer.customer_id == customer.customer_id).first()
    assert updated_customer.name == update_data["name"]
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_UPDATE",
        AuditLog.resource_id == str(customer.customer_id)
    ).first()
    assert audit_log is not None

def test_update_customer_nonexistent_id(client: TestClient, admin_token: str):
    """Test updating a non-existent customer"""
    nonexistent_id = uuid.uuid4()
    update_data = {
        "name": "Nonexistent Customer Update",
        "contact_email": "nonexistent@customer.com"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customers/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

def test_update_customer_non_admin(client: TestClient, customer_user_token: str, customer: Customer):
    """Test non-admin attempting to update customer"""
    update_data = {
        "name": "Unauthorized Update"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for suspending customer (POST /customers/{customer_id}/suspend)
def test_suspend_customer(client: TestClient, db: Session, admin_token: str, customer: Customer):
    """Test suspending a customer"""
    response = client.post(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUSPENDED"
    
    # Verify database update
    db.expire_all()
    suspended_customer = db.query(Customer).filter(Customer.customer_id == customer.customer_id).first()
    assert suspended_customer.status == CustomerStatus.SUSPENDED
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SUSPEND",
        AuditLog.resource_id == str(customer.customer_id)
    ).first()
    assert audit_log is not None

def test_suspend_customer_non_admin(client: TestClient, customer_user_token: str, customer: Customer):
    """Test non-admin attempting to suspend customer"""
    response = client.post(
        f"{settings.API_V1_STR}/customers/{customer.customer_id}/suspend",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

def test_suspend_nonexistent_customer(client: TestClient, admin_token: str):
    """Test suspending non-existent customer"""
    nonexistent_id = uuid.uuid4()
    response = client.post(
        f"{settings.API_V1_STR}/customers/{nonexistent_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

# Test cases for activating customer (POST /customers/{customer_id}/activate)
def test_activate_customer(client: TestClient, db: Session, admin_token: str, suspended_customer: Customer):
    """Test activating a suspended customer"""
    response = client.post(
        f"{settings.API_V1_STR}/customers/{suspended_customer.customer_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    
    # Verify database update
    db.expire_all()
    activated_customer = db.query(Customer).filter(Customer.customer_id == suspended_customer.customer_id).first()
    assert activated_customer.status == CustomerStatus.ACTIVE
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_ACTIVATE",
        AuditLog.resource_id == str(suspended_customer.customer_id)
    ).first()
    assert audit_log is not None

def test_activate_customer_non_admin(client: TestClient, customer_user_token: str, suspended_customer: Customer):
    """Test non-admin attempting to activate customer"""
    response = client.post(
        f"{settings.API_V1_STR}/customers/{suspended_customer.customer_id}/activate",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

def test_activate_nonexistent_customer(client: TestClient, admin_token: str):
    """Test activating non-existent customer"""
    nonexistent_id = uuid.uuid4()
    response = client.post(
        f"{settings.API_V1_STR}/customers/{nonexistent_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]