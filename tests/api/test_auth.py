"""
Test cases for authentication routes.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session

from app.models import AuditLog, User
from app.core.config import settings

# Test cases for login endpoint
def test_login_success(client: TestClient, db: Session):
    """Test successful login with valid credentials"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "admin@example.com", "password": "adminpassword"}
    )
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "LOGIN"
    ).first()
    assert audit_log is not None

def test_login_wrong_password(client: TestClient, db: Session):
    """Test login with wrong password"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "admin@example.com", "password": "wrongpassword"}
    )
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect email or password"
    # Check audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.action_type == "LOGIN_FAILED"
    ).first()
    assert audit_log is not None

def test_login_nonexistent_user(client: TestClient, db: Session):
    """Test login with non-existent user"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "nonexistent@example.com", "password": "anypassword"}
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect email or password"

def test_login_suspended_user(client: TestClient, db: Session):
    """Test login with suspended user account"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "suspended@example.com", "password": "suspendedpassword"}
    )
    
    # Check response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Inactive user"

def test_token_verification_success(client: TestClient, admin_token: str):
    """Test successful token verification"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/test-token",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert data["email"] == "admin@example.com"

def test_token_verification_invalid_token(client: TestClient):
    """Test token verification with invalid token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/test-token",
        headers={"Authorization": "Bearer invalidtoken123"}
    )
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Could not validate credentials" in data["detail"]

def test_token_verification_expired_token(client: TestClient, expired_token: str):
    """Test token verification with expired token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/test-token",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    # Check response
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Could not validate credentials" in data["detail"]

def test_token_verification_no_token(client: TestClient):
    """Test token verification with no token provided"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/test-token"
    )
    
    # Check response
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_refresh_token_success(client: TestClient, admin_token: str):
    """Test successful token refresh with a valid token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify the new token is valid by using it
    test_response = client.post(
        f"{settings.API_V1_STR}/auth/test-token",
        headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert test_response.status_code == 200

@patch('app.core.security.is_token_expired')
def test_refresh_token_not_expired(mock_is_expired, client: TestClient, admin_token: str):
    """Test token refresh when token is not near expiration"""
    # Mock the token as not expired
    mock_is_expired.return_value = False
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should return the same token
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == admin_token
    assert data["token_type"] == "bearer"

def test_refresh_token_no_auth_header(client: TestClient):
    """Test token refresh without providing Authorization header"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token"
    )
    
    # Check response - should fail
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid authentication credentials" in data["detail"]


def test_refresh_token_invalid_format(client: TestClient):
    """Test token refresh with invalid Authorization header format"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        headers={"Authorization": "InvalidFormat token123"}
    )
    
    # Check response - should fail
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid authentication credentials" in data["detail"]


def test_refresh_token_invalid_token(client: TestClient):
    """Test token refresh with invalid token"""
    response = client.post(
        f"{settings.API_V1_STR}/auth/refresh-token",
        headers={"Authorization": "Bearer invalid.token.format"}
    )
    
    # Check response - should fail
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid token" in data["detail"]