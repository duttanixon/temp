"""
Test cases for City Eye analytics routes.
"""
import uuid
from datetime import date
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole, UserStatus, Device, Solution, CustomerSolution, DeviceSolution, DeviceSolutionStatus, Customer,SolutionPackage
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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
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
    
    # Verify response is a list
    assert isinstance(data, list)
    assert len(data) == 1

    # Verify device analytics item structure
    device_item = data[0]
    assert "device_id" in device_item
    assert "device_name" in device_item
    assert "device_location" in device_item
    assert "analytics_data" in device_item
    assert "error" in device_item

    
    assert device_item["device_id"] == str(device.device_id)
    assert device_item["device_name"] == device.name
    assert device_item["device_location"] == device.location
    assert device_item["error"] is None

    # Verify analytics data structure
    analytics_data = device_item["analytics_data"]
    assert "total_count" in analytics_data
    assert "age_distribution" in analytics_data
    assert "gender_distribution" in analytics_data
    assert "age_gender_distribution" in analytics_data
    assert "hourly_distribution" in analytics_data
    assert "time_series_data" in analytics_data
    
    # Verify total count structure
    assert "total_count" in analytics_data["total_count"]
    assert isinstance(analytics_data["total_count"]["total_count"], int)
    
    # Verify age distribution structure
    age_dist = analytics_data["age_distribution"]
    required_age_fields = ["under_18", "age_18_to_29", "age_30_to_49", "age_50_to_64", "over_64"]
    for field in required_age_fields:
        assert field in age_dist
        assert isinstance(age_dist[field], int)
    
    # Verify gender distribution structure
    gender_dist = analytics_data["gender_distribution"]
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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
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
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
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
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
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

    analytics_data = data[0]["analytics_data"]
    
    # Should only include requested analytics
    assert "total_count" in analytics_data
    assert "gender_distribution" in analytics_data
    
    # Should not include non-requested analytics
    assert analytics_data.get("age_distribution") is None
    assert analytics_data.get("age_gender_distribution") is None
    assert analytics_data.get("hourly_distribution") is None
    assert analytics_data.get("time_series_data") is None

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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59",
        "polygon_ids_in": ["1"],
        "polygon_ids_out": ["1"],
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
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

# Test cases for configuration and setup errors
def test_get_human_flow_analytics_no_city_eye_solution(
    client: TestClient,
    admin_token: str,
    device: Device
):
    """Test analytics when City Eye solution doesn't exist in database"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should fail
    assert response.status_code == 404
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
    
    # Check response - should return empty list (no authorized devices)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

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
    
    # Check response - should return empty list (no devices with solution deployed)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "specify at least one device_id" in data["detail"]


def test_get_human_flow_analytics_empty_device_list(
    client: TestClient,
    customer_admin_token: str,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test with empty device list"""
    filters = {
        "device_ids": [],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "specify at least one device_id" in data["detail"]

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
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
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
    analytics_data = response.json()[0]["analytics_data"]
    assert "total_count" in analytics_data
    assert analytics_data["total_count"]["total_count"] == 0

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
    analytics_data = response.json()[0]["analytics_data"]
    assert "total_count" in analytics_data
    assert analytics_data["total_count"]["total_count"] == 0

# =============================================================================
# TRAFFIC FLOW ANALYTICS TESTS
# =============================================================================

# Test cases for successful traffic analytics requests
def test_get_traffic_flow_analytics_admin_all_includes(
    client: TestClient, 
    db: Session, 
    admin_token: str, 
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test admin successfully getting traffic flow analytics with all data types"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={
            "include_total_count": True,
            "include_vehicle_type_distribution": True,
            "include_hourly_distribution": True,
            "include_time_series": True
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response is a list
    assert isinstance(data, list)
    assert len(data) == 1
    
    # Verify device analytics item structure
    device_item = data[0]
    assert "device_id" in device_item
    assert "device_name" in device_item
    assert "device_location" in device_item
    assert "analytics_data" in device_item
    assert "error" in device_item
    
    assert device_item["device_id"] == str(device.device_id)
    assert device_item["device_name"] == device.name
    assert device_item["device_location"] == device.location
    assert device_item["error"] is None
    
    # Verify analytics data structure
    analytics_data = device_item["analytics_data"]
    assert "total_count" in analytics_data
    assert "vehicle_type_distribution" in analytics_data
    assert "hourly_distribution" in analytics_data
    assert "time_series_data" in analytics_data
    
    # Verify total count structure
    assert "total_count" in analytics_data["total_count"]
    assert isinstance(analytics_data["total_count"]["total_count"], int)
    
    # Verify vehicle type distribution structure
    vehicle_dist = analytics_data["vehicle_type_distribution"]
    required_vehicle_fields = ["large", "normal", "bicycle", "motorcycle"]
    for field in required_vehicle_fields:
        assert field in vehicle_dist
        assert isinstance(vehicle_dist[field], int)

def test_get_traffic_flow_analytics_engineer_success(
    client: TestClient,
    engineer_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test engineer successfully getting traffic flow analytics"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

def test_get_traffic_flow_analytics_customer_user_success(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test customer user successfully getting traffic analytics for their devices"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

def test_get_traffic_flow_analytics_selective_includes(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test traffic analytics with selective include parameters"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={
            "include_total_count": True,
            "include_vehicle_type_distribution": True,
            "include_hourly_distribution": False,
            "include_time_series": False
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    analytics_data = data[0]["analytics_data"]
    
    # Should only include requested analytics
    assert "total_count" in analytics_data
    assert "vehicle_type_distribution" in analytics_data
    
    # Should not include non-requested analytics
    assert analytics_data.get("hourly_distribution") is None
    assert analytics_data.get("time_series_data") is None

def test_get_traffic_flow_analytics_with_optional_filters(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test traffic analytics with additional optional filters"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59",
        "polygon_ids_in": ["1"],
        "polygon_ids_out": ["1"],
        "vehicle_types": ["large", "normal"]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "analytics_data" in data[0]
    assert "total_count" in data[0]["analytics_data"]

# Test cases for configuration and setup errors
def test_get_traffic_flow_analytics_no_city_eye_solution(
    client: TestClient,
    admin_token: str,
    device: Device
):
    """Test traffic analytics when City Eye solution doesn't exist in database"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not configured" in data["detail"]

# Test cases for customer authorization failures
def test_get_traffic_flow_analytics_customer_no_solution_access(
    client: TestClient,
    customer_admin_token: str,
    device: Device,
    city_eye_solution: Solution
):
    """Test customer user without City Eye solution access"""
    filters = {
        "device_ids": [str(device.device_id)],
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-12-31T23:59:59"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "does not have access" in data["detail"]

def test_get_traffic_flow_analytics_customer_different_device(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should return empty list (no authorized devices)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_traffic_flow_analytics_device_no_city_eye_deployed(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should return empty list (no devices with solution deployed)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_traffic_flow_analytics_user_no_customer(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
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
def test_get_traffic_flow_analytics_no_device_ids(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "specify at least one device_id" in data["detail"]

def test_get_traffic_flow_analytics_empty_device_list(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should require device selection
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "specify at least one device_id" in data["detail"]

def test_get_traffic_flow_analytics_missing_required_fields(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be validation error
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

# Test cases for authentication (shared between human and traffic)
def test_get_traffic_flow_analytics_unauthorized(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be unauthorized
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_get_traffic_flow_analytics_invalid_token(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": "Bearer invalid-token"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Could not validate credentials" in data["detail"]

def test_get_traffic_flow_analytics_expired_token(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
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
def test_get_traffic_flow_analytics_future_dates(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should succeed but with zero data
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["analytics_data"]["total_count"]["total_count"] == 0

def test_get_traffic_flow_analytics_end_before_start(
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
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should succeed but with zero data
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["analytics_data"]["total_count"]["total_count"] == 0

# Test cases for multiple devices
def test_get_traffic_flow_analytics_multiple_devices(
    client: TestClient,
    admin_token: str,
    device: Device,
    raspberry_device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data,
    db: Session
):
    """Test traffic analytics with multiple devices"""
    # Create device solution for raspberry device

    solution_package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=city_eye_solution.solution_id,
        name=f"test-package-for-{city_eye_solution.name}",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key=f"solutions/{city_eye_solution.name}/package.zip",
    )
    db.add(solution_package)
    db.commit()
    db.refresh(solution_package)

    raspberry_device_solution = DeviceSolution(
        id=uuid.uuid4(),
        device_id=raspberry_device.device_id,
        solution_id=city_eye_solution.solution_id,
        status=DeviceSolutionStatus.ACTIVE,
        package_id=solution_package.package_id,
        version_deployed="1.0.0",
        configuration={"param1": "value1"}
    )
    db.add(raspberry_device_solution)
    db.commit()
    
    filters = {
        "device_ids": [str(device.device_id), str(raspberry_device.device_id)],
        "start_time": "2025-01-01T00:00:00+09:00",
        "end_time": "2025-12-31T23:59:59+09:00"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-flow",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
        params={"include_total_count": True}
    )
    
    # Check response - should include both devices
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    device_ids = [item["device_id"] for item in data]
    assert str(device.device_id) in device_ids
    assert str(raspberry_device.device_id) in device_ids


# Test cases for human-direction analytics
def test_get_human_direction_analytics_success(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_analytics_data
):
    """Test successful retrieval of human direction analytics."""
    today = date.today().isoformat()
    filters = {
        "device_ids": [str(device.device_id)],
        "dates": [today],
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/human-direction",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    device_item = data[0]
    assert "direction_data" in device_item
    assert "detectionZones" in device_item["direction_data"]

# Test cases for traffic-direction analytics
def test_get_traffic_direction_analytics_success(
    client: TestClient,
    admin_token: str,
    device: Device,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution,
    city_eye_device_solution: DeviceSolution,
    city_eye_traffic_data
):
    """Test successful retrieval of traffic direction analytics."""
    today = date.today().isoformat()
    filters = {
        "device_ids": [str(device.device_id)],
        "dates": [today],
    }

    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/traffic-direction",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=filters,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    device_item = data[0]
    assert "direction_data" in device_item
    assert "detectionZones" in device_item["direction_data"]

@patch('app.utils.aws_iot_commands.iot_command_service.send_xlines_config_update')
def test_polygon_xlines_config_success(
    mock_send_config,
    client: TestClient,
    db: Session,  # Add the database session fixture here
    admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test successful update of polygon xlines config."""
    # 💡 Assign a `thing_name` to the device to pass the provisioning check
    # device.thing_name = "test-thing-for-pytest"
    # db.add(device)
    # db.commit()
    # db.refresh(device)
    
    mock_send_config.return_value = True
    config_data = {
        "device_id": str(active_device.device_id),
        "detectionZones": [
            {
                "polygonId": "1",
                "name": "Zone 1",
                "vertices": [
                    {"vertexId": "1-1", "position": {"x": 10, "y": 20}},
                    {"vertexId": "1-2", "position": {"x": 100, "y": 120}}
                ],
                "center": {
                    "startPoint": {"lat": 35.0, "lng": 139.0},
                    "endPoint": {"lat": 35.1, "lng": 139.1}
                }
            }
        ]
    }

    response = client.post(
        f"{settings.API_V1_STR}/analytics/city-eye/polygon-xlines-config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=config_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    mock_send_config.assert_called_once()

# Test cases for thresholds
def test_get_threshold_config_success(
    client: TestClient,
    admin_token: str,
    customer: Customer,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test successful retrieval of threshold config."""
    response = client.get(
        f"{settings.API_V1_STR}/analytics/city-eye/thresholds/{customer.customer_id}/{city_eye_solution.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == str(customer.customer_id)
    assert data["solution_id"] == str(city_eye_solution.solution_id)
    assert "thresholds" in data

def test_update_threshold_config_success(
    client: TestClient,
    admin_token: str,
    customer: Customer,
    city_eye_solution: Solution,
    city_eye_customer_solution: CustomerSolution
):
    """Test successful update of threshold config."""
    update_data = {
        "customer_id": str(customer.customer_id),
        "solution_id": str(city_eye_solution.solution_id),
        "thresholds": {
            "traffic_count_thresholds": [10, 20, 30],
            "human_count_thresholds": [50, 100]
        }
    }

    response = client.put(
        f"{settings.API_V1_STR}/analytics/city-eye/thresholds",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["thresholds"]["traffic_count_thresholds"] == [10, 20, 30]
    assert data["thresholds"]["human_count_thresholds"] == [50, 100]