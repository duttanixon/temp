"""
Test cases for user management routes.
"""
import pytest
import json
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models import User, UserRole, UserStatus, Customer
from app.core.config import settings
from app.crud.user import user as user_crud

# Test cases for current user endpoint (GET /users/me)
@pytest.mark.asyncio
async def test_read_user_me(client: TestClient, customer_admin_token: str, customer_admin_user: User, customer: Customer):
    """Test getting current user information including customer details"""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == customer_admin_user.email
    assert "user_id" in data
    assert str(data["user_id"]) == str(customer_admin_user.user_id)

    # Check customer information is included
    assert "customer" in data
    assert data["customer"] is not None
    assert "customer_id" in data["customer"]
    assert str(data["customer"]["customer_id"]) == str(customer.customer_id)
    assert data["customer"]["name"] == customer.name

@pytest.mark.asyncio
async def test_read_user_me_no_token(client: TestClient):
    """Test getting current user without authentication"""
    response = client.get(
        f"{settings.API_V1_STR}/users/me"
    )
    
    # Check response
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_read_user_me_without_customer(client: TestClient, admin_token: str, admin_user: User):
    """Test getting admin user info who doesn't belong to a customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_user.email
    assert "user_id" in data
    assert str(data["user_id"]) == str(admin_user.user_id)
    
    # Check customer information is null for admin
    assert "customer" in data
    assert data["customer"] is None

# Test cases for update current user endpoint (PUT /users/me)
@pytest.mark.asyncio
async def test_update_user_me(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user: User):
    """Test updating current user information"""
    update_data = {
        "first_name": "Updated",
        "last_name": "Names"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    assert data["email"] == customer_admin_user.email
    
    # Check database record was updated
    await db.commit()
    result = await db.execute(select(User).filter(User.user_id == customer_admin_user.user_id))
    updated_user = result.scalars().first()
    assert updated_user.first_name == update_data["first_name"]
    
    # Check audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "USER_UPDATE",
        AuditLog.user_id == customer_admin_user.user_id
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_update_user_me_email(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user: User):
    """Test updating user email"""
    update_data = {
        "email": "newemail@example.com"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    
    # Check database record was updated
    await db.commit()
    result = await db.execute(select(User).filter(User.user_id == customer_admin_user.user_id))
    updated_user = result.scalars().first()
    assert updated_user.email == update_data["email"]

@pytest.mark.asyncio
async def test_update_user_me_invalid_email(client: TestClient, customer_admin_token: str):
    """Test updating user with invalid email format"""
    update_data = {
        "email": "invalid.com"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should fail validation
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

# Test cases for change password endpoint (POST /users/password)
@pytest.mark.asyncio
async def test_change_password(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user: User):
    """Test changing user password"""
    password_data = {
        "current_password": "customeradminpassword",
        "new_password": "newpassword123"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/password",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=password_data
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify new password works by trying to authenticate
    await db.commit()
    authenticated_user = await user_crud.authenticate(
        db, 
        email=customer_admin_user.email, 
        password=password_data["new_password"]
    )
    assert authenticated_user is not None
    assert authenticated_user.user_id == customer_admin_user.user_id
    
    # Check audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "PASSWORD_CHANGE",
        AuditLog.user_id == customer_admin_user.user_id
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_change_password_incorrect_current(client: TestClient, customer_admin_token: str):
    """Test changing password with incorrect current password"""
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users/password",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=password_data
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect password"

# Test unified user listing endpoint
@pytest.mark.asyncio
async def test_get_all_users_admin(client: TestClient, admin_token: str):
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

@pytest.mark.asyncio
async def test_get_customer_users_as_customer_admin(client: TestClient, customer_admin_token: str, customer_admin_user: User):
    """Test customer admin getting users for their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All users should belong to the customer admin's customer
    for user_item in data:
        assert str(user_item["customer_id"]) == str(customer_admin_user.customer_id)


@pytest.mark.asyncio
async def test_get_other_customer_users_as_customer_admin(client: TestClient, customer_admin_token: str, suspended_customer: User):
    """Test customer admin attempting to get users from a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users?customer_id={suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]

@pytest.mark.asyncio
async def test_create_user_admin(client: TestClient, db: AsyncSession, admin_token: str, customer: User):
    """Test admin creating a new user"""
    # Mock the email sending function
    with patch('app.utils.email.send_welcome_email') as mock_send_email:
        mock_send_email.return_value = True
        
        user_data = {
            "email": "newuser@example.com",
            "password": "newuserpassword",
            "first_name": "New",
            "last_name": "User",
            "role": "CUSTOMER_ADMIN",
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
        await db.commit()
        result = await db.execute(select(User).filter(User.email == user_data["email"]))
        created_user = result.scalars().first()
        assert created_user is not None
        
        # Verify audit log
        result = await db.execute(select(AuditLog).filter(
            AuditLog.action_type == "USER_CREATE",
            AuditLog.resource_type == "USER",
            AuditLog.resource_id == str(created_user.user_id)
        ))
        audit_log = result.scalars().first()
        assert audit_log is not None
        
        # Password shouldn't be in the response
        assert "password" not in data

@pytest.mark.asyncio
async def test_create_user_customer_admin(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user: User):
    """Test customer admin creating a user for their customer"""
    with patch('app.utils.email.send_welcome_email') as mock_send_email:
        mock_send_email.return_value = True
        
        user_data = {
            "email": "newcustomeruser@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "Customer User",
            "role": "CUSTOMER_ADMIN"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/users",
            headers={"Authorization": f"Bearer {customer_admin_token}"},
            json=user_data
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]
        assert str(data["customer_id"]) == str(customer_admin_user.customer_id)
        
        # Verify user was created in database
        await db.commit()
        result = await db.execute(select(User).filter(User.email == user_data["email"]))
        created_user = result.scalars().first()
        assert created_user is not None
        assert created_user.customer_id == customer_admin_user.customer_id


@pytest.mark.asyncio
async def test_create_user_with_customer_id_param(client: TestClient, db: AsyncSession, admin_token: str, customer: User):
    """Test creating user with customer_id as a query parameter"""
    with patch('app.utils.email.send_welcome_email') as mock_send_email:
        mock_send_email.return_value = True
        
        user_data = {
            "email": "paramuser@example.com",
            "password": "password123",
            "first_name": "Param",
            "last_name": "User",
            "role": "CUSTOMER_ADMIN"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/users?customer_id={customer.customer_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=user_data
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert str(data["customer_id"]) == str(customer.customer_id)


@pytest.mark.asyncio
async def test_create_admin_role_as_customer_admin(client: TestClient, customer_admin_token: str):
    """Test customer admin attempting to create a system admin"""
    user_data = {
        "email": "newsystemadmin@example.com",
        "password": "password123",
        "first_name": "New",
        "last_name": "System Admin",
        "role": "ADMIN"  # Not allowed for customer_admin to create
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Customer admins can only create other customer admin" in data["detail"]


@pytest.mark.asyncio
async def test_create_user_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: User):
    """Test customer admin attempting to create user for different customer"""
    user_data = {
        "email": "differentcustomer@example.com",
        "password": "password123",
        "first_name": "Different",
        "last_name": "Customer",
        "role": "CUSTOMER_ADMIN",
        "customer_id": str(suspended_customer.customer_id)
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=user_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]


@pytest.mark.asyncio
async def test_create_user_existing_email(client: TestClient, admin_token: str, customer_admin_user: User):
    """Test creating user with existing email"""
    user_data = {
        "email": customer_admin_user.email,  # Already exists
        "password": "newpassword",
        "first_name": "Duplicate",
        "last_name": "User",
        "role": "CUSTOMER_ADMIN"
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

# Test get user by ID
@pytest.mark.asyncio
async def test_get_user_by_id_admin(client: TestClient, admin_token: str, customer_admin_user2: User):
    """Test admin getting a specific user by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["user_id"]) == str(customer_admin_user2.user_id)
    assert data["email"] == customer_admin_user2.email

@pytest.mark.asyncio
async def test_get_user_by_id_customer_admin_same_customer(client: TestClient, customer_admin_token: str, customer_admin_user2: User):
    """Test customer admin getting a user from their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["user_id"]) == str(customer_admin_user2.user_id)

@pytest.mark.asyncio
async def test_get_user_by_id_customer_admin_different_customer(client: TestClient, customer_admin_token: str, admin_user: User):
    """Test customer admin attempting to get user from different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_get_user_by_id_regular_user(client: TestClient, customer_admin_token: str, admin_user: User):
    """Test regular user attempting to get user by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_user_by_id_non_admin(client: TestClient, customer_admin_token: str, admin_user: User):
    """Test non-admin attempting to get user by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_admin(client: TestClient, db: AsyncSession, admin_token: str, customer_admin_user2: User):
    """Test admin updating a user"""
    update_data = {
        "first_name": "Admin",
        "last_name": "Updated",
        "role": "CUSTOMER_ADMIN"  # Change role
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["role"] == update_data["role"]
    
    # Verify database updates
    await db.commit()
    result = await db.execute(select(User).filter(User.user_id == customer_admin_user2.user_id))
    updated_user = result.scalars().first()
    assert updated_user.role == UserRole.CUSTOMER_ADMIN
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "USER_UPDATE",
        AuditLog.resource_id == str(customer_admin_user2.user_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_update_user_customer_admin_same_customer(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user2: User):
    """Test customer admin updating a user from their customer"""
    update_data = {
        "first_name": "Customer Admin",
        "last_name": "Updated"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]

@pytest.mark.asyncio
async def test_update_user_customer_admin_different_customer(client: TestClient, customer_admin_token: str, admin_user: User):
    """Test customer admin attempting to update user from different customer"""
    update_data = {
        "first_name": "Unauthorized",
        "last_name": "Update"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]

# Test suspend user endpoint
@pytest.mark.asyncio
async def test_suspend_user_admin(client: TestClient, db: AsyncSession, admin_token: str, customer_admin_user2: User):
    """Test admin suspending a user"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUSPENDED"
    
    # Verify database update
    await db.commit()
    result = await db.execute(select(User).filter(User.user_id == customer_admin_user2.user_id))
    suspended_user = result.scalars().first()
    assert suspended_user.status == UserStatus.SUSPENDED
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "USER_SUSPEND",
        AuditLog.resource_id == str(customer_admin_user2.user_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_suspend_user_customer_admin_same_customer(client: TestClient, db: AsyncSession, customer_admin_token: str, customer_admin_user2: User):
    """Test customer admin suspending a user from their customer"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{customer_admin_user2.user_id}/suspend",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUSPENDED"

@pytest.mark.asyncio
async def test_suspend_user_customer_admin_different_customer(client: TestClient, customer_admin_token: str, admin_user: User):
    """Test customer admin attempting to suspend user from different customer"""
    response = client.post(
        f"{settings.API_V1_STR}/users/{admin_user.user_id}/suspend",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "other customers" in data["detail"]

@pytest.mark.asyncio
async def test_suspend_self(client: TestClient, admin_token: str, admin_user: User):
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


@pytest.mark.asyncio
async def test_activate_user(client: TestClient, db: AsyncSession, admin_token: str, suspended_user: User):
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
    await db.commit()
    result = await db.execute(select(User).filter(User.user_id == suspended_user.user_id))
    activated_user = result.scalars().first()
    assert activated_user.status == UserStatus.ACTIVE
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "USER_ACTIVATE",
        AuditLog.resource_id == str(suspended_user.user_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

    
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