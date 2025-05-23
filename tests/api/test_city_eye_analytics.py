"""
Test cases for City Eye analytics routes.
"""
import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole, UserStatus, Device, Solution, CustomerSolution, DeviceSolution
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from datetime import timedelta

# Test cases for successful analytics requests
def test_get_human_flow_analytics_admin_all_includes(
    client: TestClient, 
    db: Session, 
    admin_token: str, 
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test admin successfully getting human flow analytics with all data types"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={
            "include_total_count": True,
            "include_age_distribution": True,
            "include_gender_distribution": True,
            "include_age_gender_distribution": True,
            "include_hourly_distribution": True,
            "include_time_series": True
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "total_count" in data
    assert "age_distribution" in data
    assert "gender_distribution" in data
    assert "age_gender_distribution" in data
    assert "hourly_distribution" in data
    assert "time_series_data" in data
    
    # Verify total count structure
    assert "total_count" in data["total_count"]
    assert isinstance(data["total_count"]["total_count"], int)
    
    # Verify age distribution structure
    age_dist = data["age_distribution"]
    required_age_fields = ["under_18", "age_18_to_29", "age_30_to_49", "age_50_to_64", "over_64"]
    for field in required_age_fields:
        assert field in age_dist
        assert isinstance(age_dist[field], int)
    
    # Verify gender distribution structure
    gender_dist = data["gender_distribution"]
    assert "male" in gender_dist
    assert "female" in gender_dist
    assert isinstance(gender_dist["male"], int)
    assert isinstance(gender_dist["female"], int)

def test_get_human_flow_analytics_engineer_success(
    client: TestClient,
    engineer_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test engineer successfully getting human flow analytics"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data

def test_get_human_flow_analytics_customer_user_success(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test customer user successfully getting analytics for their devices"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data

def test_get_human_flow_analytics_selective_includes(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test analytics with selective include parameters"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={
            "include_total_count": True,
            "include_age_distribution": False,
            "include_gender_distribution": True,
            "include_age_gender_distribution": False,
            "include_hourly_distribution": False,
            "include_time_series": False
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Should only include requested analytics
    assert "total_count" in data
    assert "gender_distribution" in data
    
    # Should not include non-requested analytics
    assert data.get("age_distribution") is None
    assert data.get("age_gender_distribution") is None
    assert data.get("hourly_distribution") is None
    assert data.get("time_series_data") is None

def test_get_human_flow_analytics_with_optional_filters(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test analytics with additional optional filters"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00",
        "polygon_ids_in": ["entrance_1"],
        "polygon_ids_out": ["exit_1"],
        "genders": ["male", "female"],
        "age_groups": ["18_to_29", "30_to_49"]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data

# Test cases for configuration and setup errors
def test_get_human_flow_analytics_no_city_eye_solution(
    client: TestClient,
    admin_token: str,
    device: Device
):
    """Test analytics when City Eye solution doesn't exist in database"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should fail
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "not configured" in data["detail"]

# Test cases for customer authorization failures
def test_get_human_flow_analytics_customer_no_solution_access(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    city_eye_solution: Solution
):
    """Test customer user without City Eye solution access"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "does not have access" in data["detail"]

def test_get_human_flow_analytics_customer_different_device(
    client: TestClient,
    customer_admin_token: str,
    suspended_customer,
    admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    db: Session
):
    """Test customer user accessing device from different customer"""
    # Create device for suspended customer
    device_data = {
        "description": "Device for different customer",
        "mac_address": "FF:EE:DD:CC:BB:AA",
        "serial_number": "SNDIFFERENT123",
        "device_type": "NVIDIA_JETSON",
        "customer_id": str(suspended_customer.customer_id)
    }
    
    create_response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    created_device = create_response.json()
    
    filters = {
        "device_ids": [created_device["device_id"]],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Access denied" in data["detail"]

def test_get_human_flow_analytics_device_no_city_eye_deployed(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test accessing device without City Eye solution deployed"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Access denied" in data["detail"]

def test_get_human_flow_analytics_nonexistent_device(
    client: TestClient,
    customer_admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test accessing non-existent device"""
    nonexistent_device_id = uuid.uuid4()
    
    filters = {
        "device_ids": [str(nonexistent_device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Access denied" in data["detail"]

def test_get_human_flow_analytics_user_no_customer(
    client: TestClient,
    db: Session,
    city_eye_solution: Solution
):
    """Test user without associated customer"""
    # Create user without customer
    orphan_user = User(
        user_id=uuid.uuid4(),
        email="orphan@example.com",
        password_hash=get_password_hash("password"),
        first_name="Orphan",
        last_name="User",
        role=UserRole.CUSTOMER_ADMIN,
        customer_id=None,  # No customer association
        status=UserStatus.ACTIVE
    )
    db.add(orphan_user)
    db.commit()
    
    orphan_token = create_access_token(
        subject=str(orphan_user.user_id),
        expires_delta=timedelta(minutes=30),
        role=UserRole.CUSTOMER_ADMIN.value
    )
    
    filters = {
        "device_ids": [str(uuid.uuid4())],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {orphan_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "not associated with any customer" in data["detail"]

# Test cases for request validation
def test_get_human_flow_analytics_no_device_ids(
    client: TestClient,
    customer_admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test without providing device IDs"""
    filters = {
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "select at least one device" in data["detail"]


def test_get_human_flow_analytics_empty_device_list(
    client: TestClient,
    customer_admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test with empty device list"""
    filters = {
        "device_ids": [],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "select at least one device" in data["detail"]

def test_get_human_flow_analytics_missing_required_fields(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution
):
    """Test with missing required fields in request"""
    # Missing start_time and end_time
    filters = {
        "device_ids": [str(device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be validation error
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

# Test cases for authentication
def test_get_human_flow_analytics_unauthorized(
    client: TestClient,
    device: Device,
    city_eye_solution: Solution
):
    """Test without authentication token"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be unauthorized
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_get_human_flow_analytics_invalid_token(
    client: TestClient,
    device: Device,
    city_eye_solution: Solution
):
    """Test with invalid authentication token"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": "Bearer invalid-token"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Could not validate credentials" in data["detail"]

def test_get_human_flow_analytics_expired_token(
    client: TestClient,
    expired_token: str,
    device: Device,
    city_eye_solution: Solution
):
    """Test with expired authentication token"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {expired_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Could not validate credentials" in data["detail"]

# Test cases for edge cases and data scenarios
def test_get_human_flow_analytics_future_dates(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution
):
    """Test with future dates (should work but return no data)"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2030-01-01T00:00:00+09:00",
        "end_time": "2030-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should succeed but with zero data
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert data["total_count"]["total_count"] == 0

def test_get_human_flow_analytics_end_before_start(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution
):
    """Test with end time before start time"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-12-31T23:59:59+09:00",
        "end_time": "2025-01-01T00:00:00+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should succeed but with zero data
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert data["total_count"]["total_count"] == 0

# Test cases for partial access (some devices authorized, some not)
def test_get_human_flow_analytics_mixed_device_access(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    suspended_customer,
    admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    db: Session
):
    """Test customer user with mixed device access (some authorized, some not)"""
    # Create device for suspended customer
    device_data = {
        "description": "Device for different customer",
        "mac_address": "FF:EE:DD:CC:BB:AA",
        "serial_number": "SNDIFFERENT123",
        "device_type": "NVIDIA_JETSON",
        "customer_id": str(suspended_customer.customer_id)
    }
    
    create_response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    other_device = create_response.json()
    
    # Try to access both devices - one authorized, one not
    filters = {
        "device_ids": [str(device.device_id), other_device["device_id"]],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden because of unauthorized device
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Access denied" in data["detail"]