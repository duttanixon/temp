"""
Test cases for user management routes.
"""
import pytest
import json
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User, UserRole, UserStatus
from app.core.config import settings
from app.crud.user import user as user_crud

# Test cases for current user endpoint (GET /users/me)
def test_read_user_me(client: TestClient, customer_user_token: str, customer_user: User):
    """Test getting current user information"""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == customer_user.email
    assert "user_id" in data
    assert str(data["user_id"]) == str(customer_user.user_id)

def test_read_user_me_no_token(client: TestClient):
    """Test getting current user without authentication"""
    response = client.get(
        f"{settings.API_V1_STR}/users/me"
    )
    
    # Check response
    assert response.status_code == 401

# Test cases for update current user endpoint (PUT /users/me)
def test_update_user_me(client: TestClient, db: Session, customer_user_token: str, customer_user: User):
    """Test updating current user information"""
    update_data = {
        "first_name": "Updated",
        "last_name": "Names"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    assert data["email"] == customer_user.email
    
    # Check database record was updated
    db.expire_all()
    updated_user = db.query(User).filter(User.user_id == customer_user.user_id).first()
    assert updated_user.first_name == update_data["first_name"]
    
    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "USER_UPDATE",
        AuditLog.user_id == customer_user.user_id
    ).first()
    assert audit_log is not None

def test_update_user_me_email(client: TestClient, db: Session, customer_user_token: str, customer_user: User):
    """Test updating user email"""
    update_data = {
        "email": "newemail@example.com"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    
    # Check database record was updated
    db.expire_all()
    updated_user = db.query(User).filter(User.user_id == customer_user.user_id).first()
    assert updated_user.email == update_data["email"]

def test_update_user_me_invalid_email(client: TestClient, customer_user_token: str):
    """Test updating user with invalid email format"""
    update_data = {
        "email": "invalid.com"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response - should fail validation
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

# Test cases for change password endpoint (POST /users/password)
def test_change_password(client: TestClient, db: Session, customer_user_token: str, customer_user: User):
    """Test changing user password"""
    password_data = {
        "current_password": "customeruserpassword",
        "new_password": "newpassword123"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/password",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=password_data
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify new password works by trying to authenticate
    db.expire_all()
    authenticated_user = user_crud.authenticate(
        db, 
        email=customer_user.email, 
        password=password_data["new_password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.user_id == customer_user.user_id
    
    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "PASSWORD_CHANGE",
        AuditLog.user_id == customer_user.user_id
    ).first()
    assert audit_log is not None

def test_change_password_incorrect_current(client: TestClient, customer_user_token: str):
    """Test changing password with incorrect current password"""
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/password",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=password_data
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect password"

def test_get_all_users_admin(client: TestClient, admin_token: str):
    """Test admin getting all users"""
    response = client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5  # We created 5 test users in our seed data


def test_get_all_users_non_admin(client: TestClient, customer_user_token: str):
    """Test non-admin attempting to get all users"""
    response = client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

def test_create_user_admin(client: TestClient, db: Session, admin_token: str, customer: User):
    """Test admin creating a new user"""
    # Mock the email sending function
    with patch('app.utils.email.send_welcome_email') as mock_send_email:
        mock_send_email.return_value = True
        
        user_data = {
            "email": "newuser@example.com",
            "password": "newuserpassword",
            "first_name": "New",
            "last_name": "User",
            "role": "CUSTOMER_USER",
            "customer_id": str(customer.customer_id)
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert "user_id" in data
        
        # Verify user was created in the database
        db.expire_all()
        created_user = db.query(User).filter(User.email == user_data["email"]).first()
        assert created_user is not None
        
        # Verify audit log
        audit_log = db.query(AuditLog).filter(
            AuditLog.action_type == "USER_CREATE",
            AuditLog.resource_type == "USER",
            AuditLog.resource_id == str(created_user.user_id)
        ).first()
        assert audit_log is not None
        
        # Password shouldn't be in the response
        assert "password" not in data

def test_create_user_existing_email(client: TestClient, admin_token: str, customer_user: User):
    """Test creating user with existing email"""
    user_data = {
        "email": customer_user.email,  # Already exists
        "password": "newpassword",
        "first_name": "Duplicate",
        "last_name": "User",
        "role": "CUSTOMER_USER"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=user_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"]

def test_get_user_by_id(client: TestClient, admin_token: str, customer_user: User):
    """Test getting a specific user by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{customer_user.user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["user_id"]) == str(customer_user.user_id)
    assert data["email"] == customer_user.email


def test_get_user_by_id_non_admin(client: TestClient, customer_user_token: str, admin_user: User):
    """Test non-admin attempting to get user by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403


def test_update_user_admin(client: TestClient, db: Session, admin_token: str, customer_user: User):
    """Test admin updating a user"""
    update_data = {
        "first_name": "Admin",
        "last_name": "Updated",
        "role": "CUSTOMER_ADMIN"  # Change role
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/{customer_user.user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["role"] == update_data["role"]
    
    # Verify database updates
    db.expire_all()
    updated_user = db.query(User).filter(User.user_id == customer_user.user_id).first()
    assert updated_user.role == UserRole.CUSTOMER_ADMIN
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "USER_UPDATE",
        AuditLog.resource_id == str(customer_user.user_id)
    ).first()
    assert audit_log is not None


def test_suspend_user(client: TestClient, db: Session, admin_token: str, customer_user: User):
    """Test suspending a user"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{customer_user.user_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUSPENDED"
    
    # Verify database update
    db.expire_all()
    suspended_user = db.query(User).filter(User.user_id == customer_user.user_id).first()
    assert suspended_user.status == UserStatus.SUSPENDED
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "USER_SUSPEND",
        AuditLog.resource_id == str(customer_user.user_id)
    ).first()
    assert audit_log is not None

def test_suspend_self(client: TestClient, admin_token: str, admin_user: User):
    """Test attempting to suspend own account"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Cannot suspend yourself" in data["detail"]


def test_activate_user(client: TestClient, db: Session, admin_token: str, suspended_user: User):
    """Test activating a suspended user"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{suspended_user.user_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    
    # Verify database update
    db.expire_all()
    activated_user = db.query(User).filter(User.user_id == suspended_user.user_id).first()
    assert activated_user.status == UserStatus.ACTIVE
    
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "USER_ACTIVATE",
        AuditLog.resource_id == str(suspended_user.user_id)
    ).first()
    assert audit_log is not None


# Test cases for customer admin operations

def test_get_users_by_customer(client: TestClient, customer_admin_token: str, customer: User):
    """Test customer admin getting users for their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All users should belong to the customer
    for user in data:
        assert str(user["customer_id"]) == str(customer.customer_id)

def test_get_users_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: User):
    """Test customer admin attempting to get users for a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users/customer/{suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]



def test_create_customer_user(client: TestClient, db: Session, customer_admin_token: str, customer: User):
    """Test customer admin creating a new user for their customer"""
    # # Mock the email sending function
    # with patch('app.utils.email.send_welcome_email') as mock_send_email:
    #     mock_send_email.return_value = True
        
    user_data = {
        "email": "newcustomeruser@example.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "Customer User",
        "role": "CUSTOMER_USER"
    }
        
    response = client.post(
        f"{settings.API_V1_STR}/users/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
        
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]
    assert str(data["customer_id"]) == str(customer.customer_id)
        
    # Verify user was created in database
    db.expire_all()
    created_user = db.query(User).filter(User.email == user_data["email"]).first()
    assert created_user is not None
    assert created_user.customer_id == customer.customer_id
        
    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "USER_CREATE",
        AuditLog.resource_id == str(created_user.user_id)
    ).first()
    assert audit_log is not None


def test_create_customer_admin_role(client: TestClient, customer_admin_token: str, customer: User):
    """Test customer admin creating another customer admin"""
    user_data = {
        "email": "newcustomeradmin@example.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "Customer Admin",
        "role": "CUSTOMER_ADMIN"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
    
    # Check response - should succeed
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "CUSTOMER_ADMIN"

def test_create_admin_role_as_customer_admin(client: TestClient, customer_admin_token: str, customer: User):
    """Test customer admin attempting to create a system admin"""
    user_data = {
        "email": "newsystemadmin@example.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "System Admin",
        "role": "ADMIN"  # Not allowed for customer_admin to create
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "can only create customer users or customer admins" in data["detail"]

def test_create_user_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: User):
    """Test customer admin attempting to create user for different customer"""
    user_data = {
        "email": "differentcustomer@example.com",
        "password": "password123",
        "first_name": "Different",
        "last_name": "Customer",
        "role": "CUSTOMER_USER"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/customer/{suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]

    
# def test_create_user_with_auto_password(client: TestClient, admin_token: str, customer: User):
#     """Test creating user with auto-generated password"""
    # Mock the email sending function
    # with patch('app.utils.email.send_welcome_email') as mock_send_email:
    #     mock_send_email.return_value = True
        
        # user_data = {
        #     "email": "autopass@example.com",
        #     "first_name": "Auto",
        #     "last_name": "Password",
        #     "role": "customer_user",
        #     "customer_id": str(customer.customer_id)
        # }
        
        # response = client.post(
        #     f"{settings.API_V1_STR}/users",
        #     headers={"Authorization": f"Bearer {admin_token}"},
        #     json=user_data
        # )
        # print(response.json())
        
        # # Check response
        # assert response.status_code == 200
        # data = response.json()
        # assert data["email"] == user_data["email"]
        
        # # Verify email sending was called
        # mock_send_email.assert_called_once()