"""
Test cases for device metrics routes
"""
import pytest
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import Device, User, AuditLog, Customer

@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_memory_metrics')
async def test_get_memory_metrics_admin(mock_query_memory, client: TestClient, admin_token: str, device: Device):
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


@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_memory_metrics')
async def test_get_memory_metrics_engineer(mock_query_memory, client: TestClient, engineer_token: str, device: Device):
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


@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_memory_metrics')
async def test_get_memory_metrics_customer_user_own_device(
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

@pytest.mark.asyncio
@patch('app.crud.customer.customer.get_by_id')
@patch('app.utils.aws_iot.iot_core.provision_device')
async def test_get_memory_metrics_customer_user_different_customer(
    mock_provision,
    mock_get_customer,
    client: TestClient, customer_admin_token: str, suspended_customer: Customer, admin_token: str
):
    """Test customer user attempting to get metrics for device from different customer"""
    # Mock customer with IoT Thing Group for suspended customer
    from unittest.mock import MagicMock
    customer_with_iot = MagicMock()
    customer_with_iot.customer_id = suspended_customer.customer_id
    customer_with_iot.iot_thing_group_name = "test-metrics-customer-group"
    mock_get_customer.return_value = customer_with_iot
    
    # Mock AWS IoT provisioning response to return the same thing_name as device_name
    def mock_provision_func(thing_name, device_type, mac_address, customer_group_name):
        return {
            "thing_name": thing_name,  # Return the same thing_name passed in
            "thing_arn": f"arn:aws:iot:region:account:thing/{thing_name}",
            "certificate_id": "test-metrics-cert-id",
            "certificate_arn": "arn:aws:iot:region:account:cert/test-metrics-cert-id",
            "certificate_path": "s3://bucket/certs/test-metrics-cert-id.pem",
            "private_key_path": "s3://bucket/keys/test-metrics-cert-id.key",
            "certificate_url": "https://s3.amazonaws.com/bucket/certs/test-metrics-cert-id.pem",
            "private_key_url": "https://s3.amazonaws.com/bucket/keys/test-metrics-cert-id.key"
        }
    
    mock_provision.side_effect = mock_provision_func
    
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
    device_name = created_device["thing_name"]  # thing_name should match the generated device name
    
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

@pytest.mark.asyncio
async def test_get_memory_metrics_nonexistent_device(client: TestClient, admin_token: str):
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


@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_memory_metrics')
async def test_get_memory_metrics_error(mock_query_memory, client: TestClient, admin_token: str, device: Device):
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
@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_cpu_metrics')
async def test_get_cpu_metrics_admin(mock_query_cpu, client: TestClient, admin_token: str, device: Device):
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



# Test cases for temperatue metrics endpoint (GET /device-metrics/temperatue)
@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_temperature_metrics')
async def test_get_temperature_metrics_admin(mock_query_temperature, client: TestClient, admin_token: str, device: Device):
    """Test admin getting temperature metrics for a device"""
    # Mock the timestream query function
    mock_query_temperature.return_value = {
        "series": [
            {"name": "CPU Temperature", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 66.0}]},
            {"name": "GPU Temperature", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 67.0}]}
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
        f"{settings.API_V1_STR}/device-metrics/temperature",
        params=params,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["series"]) == 2
    assert data["series"][0]["name"] == "CPU Temperature"
    assert data["series"][1]["name"] == "GPU Temperature"
    assert len(data["series"][0]["data"]) == 1
    assert data["interval"] == "5m"
    
    # Verify the query function was called with the correct parameters
    mock_query_temperature.assert_called_once()
    call_args = mock_query_temperature.call_args[0]
    assert call_args[0] == device.name
    assert call_args[3] == 5  # interval


@pytest.mark.asyncio
@patch('app.api.routes.device_metrics.query_temperature_metrics')
async def test_get_temperature_metrics_default_parameters(
    mock_query_temperature, client: TestClient, admin_token: str, device: Device
):
    """Test getting temperature metrics with default parameters"""
    # Mock the timestream query function
    mock_query_temperature.return_value = {
        "series": [
            {"name": "CPU Temperature", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 66.0}]},
            {"name": "GPU Temperature", "data": [{"timestamp": "2025-05-18T09:00:00Z", "value": 67.0}]}
        ],
        "device_name": device.name,
        "start_time": datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(hours=1),
        "end_time": datetime.now(ZoneInfo("Asia/Tokyo")),
        "interval": "5m"
    }
    
    # Use only device_name parameter, letting the other parameters use defaults
    response = client.get(
        f"{settings.API_V1_STR}/device-metrics/temperature?device_name={device.name}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify the query function was called
    mock_query_temperature.assert_called_once()
    call_args = mock_query_temperature.call_args[0]
    assert call_args[0] == device.name
    assert call_args[3] == 5  # default interval