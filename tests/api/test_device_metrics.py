"""
Test cases for device metrics routes
"""
import pytest
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Device, User, AuditLog, Customer

@patch('app.api.routes.device_metrics.query_memory_metrics')
def test_get_memory_metrics_admin(mock_query_memory, client: TestClient, admin_token: str, device: Device):
    """Test admin getting memory metrics for a device"""
    # Mock the timestream query function with fixed test data
    mock_data = {
        "series": [
            {"name": "Mem Used", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 3600.0}]},
            {"name": "Mem Free", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 550.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    # Configure the mock to return our test data
    mock_query_memory.return_value = mock_data
    
    # Define query parameters
    start_time = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1)
    end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    
    # Use params argument for proper URL encoding
    params = {
        "device_name": device.name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "interval": 5
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory",
        params=params,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check if mock was called
    mock_query_memory.assert_called_once()
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Make assertions on response structure
    assert len(data["series"]) == 2
    assert data["series"][0]["name"] == "Mem Used"
    assert data["series"][1]["name"] == "Mem Free"
    assert len(data["series"][0]["data"]) == 1
    assert data["interval"] == "5m"


@patch('app.api.routes.device_metrics.query_memory_metrics')
def test_get_memory_metrics_engineer(mock_query_memory, client: TestClient, engineer_token: str, device: Device):
    """Test engineer getting memory metrics for a device"""
    # Mock the timestream query function
    mock_query_memory.return_value = {
        "series": [
            {"name": "Mem Used", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 3600.0}]},
            {"name": "Mem Free", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 550.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory?device_name={device.name}",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["series"]) == 2


@patch('app.api.routes.device_metrics.query_memory_metrics')
def test_get_memory_metrics_customer_user_own_device(
    mock_query_memory, client: TestClient, customer_admin_token: str, device: Device
):
    """Test customer user getting memory metrics for their own device"""
    # Mock the timestream query function
    mock_query_memory.return_value = {
        "series": [
            {"name": "Mem Used", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 3600.0}]},
            {"name": "Mem Free", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 550.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory?device_name={device.name}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["series"]) == 2

def test_get_memory_metrics_customer_user_different_customer(
    client: TestClient, customer_admin_token: str, suspended_customer: Customer, admin_token: str
):
    """Test customer user attempting to get metrics for device from different customer"""
    # First create a device for the suspended customer
    device_data = {
        "description": "A test device for a different customer",
        "mac_address": "DD:EE:FF:11:22:33",
        "serial_number": "SNDIFFERENT",
        "device_type": "NVIDIA_JETSON",
        "firmware_version": "1.0.0",
        "location": "Other Location",
        "customer_id": str(suspended_customer.customer_id),
        "ip_address": "192.168.1.250"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    
    assert response.status_code == 200
    created_device = response.json()
    device_name = created_device["name"]
    
    # Now try to get metrics as customer user
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory?device_name={device_name}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]

def test_get_memory_metrics_nonexistent_device(client: TestClient, admin_token: str):
    """Test getting metrics for a non-existent device"""
    nonexistent_name = "NonExistentDevice-123"
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory?device_name={nonexistent_name}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.api.routes.device_metrics.query_memory_metrics')
def test_get_memory_metrics_error(mock_query_memory, client: TestClient, admin_token: str, device: Device):
    """Test error handling when timestream query fails"""
    # Mock the timestream query function to raise an exception
    mock_query_memory.side_effect = Exception("Timestream query error")
    
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/memory?device_name={device.name}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be internal server error
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Error" in data["detail"]


# Test cases for CPU metrics endpoint (GET /device-metrics/cpu)
@patch('app.api.routes.device_metrics.query_cpu_metrics')
def test_get_cpu_metrics_admin(mock_query_cpu, client: TestClient, admin_token: str, device: Device):
    """Test admin getting CPU metrics for a device"""
    # Mock the timestream query function
    mock_query_cpu.return_value = {
        "series": [
            {"name": "CPU Usage", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 45.0}]},
            {"name": "User CPU", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 30.0}]},
            {"name": "System CPU", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 15.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    # Define query parameters
    start_time = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1)
    end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    
    params = {
        "device_name": device.name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "interval": 5
    }

    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/cpu",
        params=params,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["series"]) == 3
    assert data["series"][0]["name"] == "CPU Usage"
    assert data["series"][1]["name"] == "User CPU"
    assert data["series"][2]["name"] == "System CPU"
    assert len(data["series"][0]["data"]) == 1
    assert data["interval"] == "5m"
    
    # Verify the query function was called with the correct parameters
    mock_query_cpu.assert_called_once()
    call_args = mock_query_cpu.call_args[0]
    assert call_args[0] == device.name
    assert call_args[3] == 5  # interval



# Test cases for disk metrics endpoint (GET /device-metrics/disk)
@patch('app.api.routes.device_metrics.query_disk_metrics')
def test_get_disk_metrics_admin(mock_query_disk, client: TestClient, admin_token: str, device: Device):
    """Test admin getting disk metrics for a device"""
    # Mock the timestream query function
    mock_query_disk.return_value = {
        "series": [
            {"name": "Disk Read", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 250.0}]},
            {"name": "Disk Write", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 120.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    # Define query parameters
    start_time = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1)
    end_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    
    params = {
        "device_name": device.name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "interval": 5
    }

    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/disk",
        params=params,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["series"]) == 2
    assert data["series"][0]["name"] == "Disk Read"
    assert data["series"][1]["name"] == "Disk Write"
    assert len(data["series"][0]["data"]) == 1
    assert data["interval"] == "5m"
    
    # Verify the query function was called with the correct parameters
    mock_query_disk.assert_called_once()
    call_args = mock_query_disk.call_args[0]
    assert call_args[0] == device.name
    assert call_args[3] == 5  # interval


@patch('app.api.routes.device_metrics.query_disk_metrics')
def test_get_disk_metrics_default_parameters(
    mock_query_disk, client: TestClient, admin_token: str, device: Device
):
    """Test getting disk metrics with default parameters"""
    # Mock the timestream query function
    mock_query_disk.return_value = {
        "series": [
            {"name": "Disk Read", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 250.0}]},
            {"name": "Disk Write", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 120.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    # Use only device_name parameter, letting the other parameters use defaults
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/disk?device_name={device.name}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify the query function was called
    mock_query_disk.assert_called_once()
    call_args = mock_query_disk.call_args[0]
    assert call_args[0] == device.name
    assert call_args[3] == 5  # default interval