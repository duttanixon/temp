"""
Test cases for device management routes
"""
import pytest
import uuid
from typing import Dict
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models import Device, DeviceStatus, DeviceType,  Customer, User, Solution, DeviceSolution
from app.core.config import settings
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from app.schemas.device import DeviceBatchStatusRequest


# Test cases for device listing (GET /devices)
@pytest.mark.asyncio
async def test_get_all_devices_admin(client: TestClient, admin_token: str):
    """Test admin getting all devices"""
    response = client.get(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should return at least one device
    assert len(data) >= 1
    

@pytest.mark.asyncio
async def test_get_devices_by_customer_admin(client: TestClient, customer_admin_token: str, customer: Customer, device: Device):
    """Test getting devices filtered by customer_id"""
    response = client.get(
        f"{settings.API_V1_STR}/devices?customer_id={customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All returned devices should belong to the specified customer
    for device_item in data:
        assert str(device_item["customer_id"]) == str(customer.customer_id)


@pytest.mark.asyncio
async def test_get_devices_customer_user_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: Customer):
    """Test customer admin attempting to get devices from a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/devices?customer_id={suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


# Test cases for device creation (POST /devices)
@pytest.mark.asyncio
@patch('app.crud.customer.customer.get_by_id')
@patch('app.utils.aws_iot.iot_core.provision_device')
async def test_create_device_admin(mock_provision, mock_get_customer, client: TestClient, db: AsyncSession, admin_token: str, customer: Customer):
    """Test admin creating a new device (now includes provisioning)"""
    # Mock customer with IoT Thing Group
    customer_with_iot = MagicMock()
    customer_with_iot.customer_id = customer.customer_id
    customer_with_iot.iot_thing_group_name = "test-customer-group"
    mock_get_customer.return_value = customer_with_iot
    
    # Mock AWS IoT provisioning response
    mock_provision.return_value = {
        "thing_name": "D-TEST123",
        "thing_arn": "arn:aws:iot:region:account:thing/D-TEST123",
        "certificate_id": "test-cert-id",
        "certificate_arn": "arn:aws:iot:region:account:cert/test-cert-id",
        "certificate_path": "s3://bucket/certs/test-cert-id.pem",
        "private_key_path": "s3://bucket/keys/test-cert-id.key",
        "certificate_url": "https://s3.amazonaws.com/bucket/certs/test-cert-id.pem",
        "private_key_url": "https://s3.amazonaws.com/bucket/keys/test-cert-id.key"
    }
    
    device_data = {
        "description": "A test device",
        "mac_address": "00:11:22:33:44:56",
        "serial_number": "SN123456789",
        "device_type": "NVIDIA_JETSON",
        "firmware_version": "1.0.0",
        "location": "Test Location",
        "customer_id": str(customer.customer_id),
        "ip_address": "192.168.1.100"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    
    # Check response - now expects DeviceProvisionResponse
    assert response.status_code == 200
    data = response.json()
    assert "device_id" in data
    assert "thing_name" in data
    assert "certificate_url" in data
    assert "private_key_url" in data
    assert "status" in data
    assert data["status"] == "PROVISIONED"  # Device should be provisioned immediately
    
    # Verify device was created in database with PROVISIONED status
    await db.commit()
    result = await db.execute(select(Device).filter(Device.device_id == uuid.UUID(data["device_id"])))
    created_device = result.scalars().first()
    assert created_device is not None
    assert created_device.mac_address == device_data["mac_address"]
    assert created_device.status == DeviceStatus.PROVISIONED
    assert created_device.thing_name is not None
    
    # Verify AWS provisioning was called
    mock_provision.assert_called_once()
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "DEVICE_CREATE",
        AuditLog.resource_id == str(created_device.device_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
@patch('app.crud.customer.customer.get_by_id')
@patch('app.utils.aws_iot.iot_core.provision_device')
async def test_create_device_engineer(mock_provision, mock_get_customer, client: TestClient, engineer_token: str, customer: Customer):
    """Test engineer creating a new device (now includes provisioning)"""
    # Mock customer with IoT Thing Group
    customer_with_iot = MagicMock()
    customer_with_iot.customer_id = customer.customer_id
    customer_with_iot.iot_thing_group_name = "test-engineer-customer-group"
    mock_get_customer.return_value = customer_with_iot
    
    # Mock AWS IoT provisioning response
    mock_provision.return_value = {
        "thing_name": "D-ENG456",
        "thing_arn": "arn:aws:iot:region:account:thing/D-ENG456",
        "certificate_id": "test-eng-cert-id",
        "certificate_arn": "arn:aws:iot:region:account:cert/test-eng-cert-id",
        "certificate_path": "s3://bucket/certs/test-eng-cert-id.pem",
        "private_key_path": "s3://bucket/keys/test-eng-cert-id.key",
        "certificate_url": "https://s3.amazonaws.com/bucket/certs/test-eng-cert-id.pem",
        "private_key_url": "https://s3.amazonaws.com/bucket/keys/test-eng-cert-id.key"
    }
    
    device_data = {
        "description": "A test device created by engineer",
        "mac_address": "BB:BB:CC:DD:EE:FF",
        "serial_number": "SN987654321",
        "device_type": "RASPBERRY_PI",
        "firmware_version": "2.0.0",
        "location": "Engineer Location",
        "customer_id": str(customer.customer_id),
        "ip_address": "192.168.1.200"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json=device_data
    )
    
    # Check response - now expects DeviceProvisionResponse
    assert response.status_code == 200
    data = response.json()
    assert "device_id" in data
    assert "thing_name" in data
    assert "certificate_url" in data
    assert "private_key_url" in data
    assert "status" in data
    assert data["status"] == "PROVISIONED"
    
    # Verify AWS provisioning was called
    mock_provision.assert_called_once()


@pytest.mark.asyncio
async def test_create_device_customer_user(client: TestClient, customer_admin_token: str, customer: Customer):
    """Test customer user attempting to create a device"""
    device_data = {
        "description": "A test device created by customer user",
        "mac_address": "12:22:33:44:55:66",
        "serial_number": "SNXXXXXXXX",
        "device_type": "NVIDIA_JETSON",
        "firmware_version": "1.0.0",
        "location": "User Location",
        "customer_id": str(customer.customer_id),
        "ip_address": "192.168.1.300"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=device_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

@pytest.mark.asyncio
async def test_create_device_duplicate_mac(client: TestClient, db: AsyncSession, admin_token: str, customer: Customer, device: Device):
    """Test creating a device with duplicate MAC address"""
    # Try to create another device with the same MAC address as an existing device
    duplicate_data = {
        "description": "Duplicate Device",
        "mac_address": device.mac_address,  # Use existing MAC address
        "serial_number": "SNDUPLICATE",
        "device_type": "NVIDIA_JETSON",
        "firmware_version": "1.0.0",
        "location": "Duplicate Location",
        "customer_id": str(customer.customer_id),
        "ip_address": "192.168.1.100"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=duplicate_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already exists" in data["detail"]

@pytest.mark.asyncio
async def test_create_device_nonexistent_customer(client: TestClient, admin_token: str):
    """Test creating a device with non-existent customer"""
    nonexistent_id = uuid.uuid4()
    device_data = {
        "description": "A test device",
        "mac_address": "99:88:77:66:55:44",
        "serial_number": "SNABCDEF",
        "device_type": "RASPBERRY_PI",
        "firmware_version": "1.0.0",
        "location": "Nowhere",
        "customer_id": str(nonexistent_id),
        "ip_address": "192.168.1.100"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer not found" in data["detail"]

# Test cases for getting a specific device (GET /devices/{device_id})
@pytest.mark.asyncio
async def test_get_device_by_id_admin(client: TestClient, admin_token: str, device: Device):
    """Test admin getting a device by ID"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["device_id"]) == str(device.device_id)
    assert data["name"] == device.name
    assert data["mac_address"] == device.mac_address


@pytest.mark.asyncio
async def test_get_device_by_id_customer_user_own_customer(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer user getting a device from their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["device_id"]) == str(device.device_id)

@pytest.mark.asyncio
@patch('app.crud.customer.customer.get_by_id')
@patch('app.utils.aws_iot.iot_core.provision_device')
async def test_get_device_by_id_customer_user_different_customer(mock_provision, mock_get_customer, client: TestClient, customer_admin_token: str, suspended_customer: Customer, admin_token: str):
    """Test customer user attempting to get a device from a different customer"""
    # Mock customer with IoT Thing Group for suspended customer
    customer_with_iot = MagicMock()
    customer_with_iot.customer_id = suspended_customer.customer_id
    customer_with_iot.iot_thing_group_name = "test-suspended-customer-group"
    mock_get_customer.return_value = customer_with_iot
    
    # Mock AWS IoT provisioning response
    mock_provision.return_value = {
        "thing_name": "D-DIFF789",
        "thing_arn": "arn:aws:iot:region:account:thing/D-DIFF789",
        "certificate_id": "test-diff-cert-id",
        "certificate_arn": "arn:aws:iot:region:account:cert/test-diff-cert-id",
        "certificate_path": "s3://bucket/certs/test-diff-cert-id.pem",
        "private_key_path": "s3://bucket/keys/test-diff-cert-id.key",
        "certificate_url": "https://s3.amazonaws.com/bucket/certs/test-diff-cert-id.pem",
        "private_key_url": "https://s3.amazonaws.com/bucket/keys/test-diff-cert-id.key"
    }
    
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
    
    # Now get the device by ID as customer user
    response = client.get(
        f"{settings.API_V1_STR}/devices/{created_device['device_id']}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]

@pytest.mark.asyncio
async def test_get_nonexistent_device(client: TestClient, admin_token: str):
    """Test getting a non-existent device"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/devices/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

# Test cases for updating a device (PUT /devices/{device_id})
@pytest.mark.asyncio
async def test_update_device_admin(client: TestClient, db: AsyncSession, admin_token: str, device: Device):
    """Test admin updating a device"""
    update_data = {
        "description": "Updated Description",
        "firmware_version": "2.0.0",
        "location": "Updated Location",
        "ip_address": "192.168.1.200"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/devices/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]
    assert data["firmware_version"] == update_data["firmware_version"]
    assert data["location"] == update_data["location"]
    
    # Verify database updates
    await db.commit()
    result = await db.execute(select(Device).filter(Device.device_id == device.device_id))
    updated_device = result.scalars().first()
    assert updated_device.description == update_data["description"]
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "DEVICE_UPDATE",
        AuditLog.resource_id == str(device.device_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None


@pytest.mark.asyncio
async def test_update_device_customer_admin(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer admin updating a device from their customer"""
    update_data = {
        "description": "Customer Admin Updated",
        "firmware_version": "3.0.0",
        "location": "New Location"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/devices/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]
    assert data["firmware_version"] == update_data["firmware_version"]
    assert data["location"] == update_data["location"]


# Test cases for decommissioning a device (POST /devices/{device_id}/decommission)
@pytest.mark.asyncio
@patch('app.utils.aws_iot.iot_core.delete_thing_certificate')
@patch('app.crud.device.device.decommission')
async def test_decommission_device(mock_decommission, mock_delete_thing, client: TestClient, db: AsyncSession, admin_token: str, active_device: Device):
    """Test decommissioning a device"""
    # Mock AWS IoT cleanup
    mock_delete_thing.return_value = True
    
    # Mock the database operation for decommissioning
    mock_decommission.return_value = Device(
        device_id=active_device.device_id,
        name=active_device.name,
        customer_id=active_device.customer_id,
        device_type=active_device.device_type,
        status=DeviceStatus.DECOMMISSIONED,
        is_online=False,                         
        created_at=datetime.now(),      
        updated_at=datetime.now()
    )
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/decommission",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DECOMMISSIONED"
    
    # Verify functions were called
    mock_delete_thing.assert_called_once()
    mock_decommission.assert_called_once()


@pytest.mark.asyncio
async def test_decommission_device_no_permission(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer user attempting to decommission a device (no permission)"""
    response = client.post(
        f"{settings.API_V1_STR}/devices/{device.device_id}/decommission",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


# Test cases for activating a device (POST /devices/{device_id}/activate)
@pytest.mark.asyncio
@patch('app.crud.device.device.activate')
async def test_activate_device(mock_activate, client: TestClient, db: AsyncSession, admin_token: str, device: Device):
    """Test activating a device"""
    # Mock the database operation for activation
    mock_activate.return_value = Device(
        device_id=device.device_id,
        name=device.name,
        customer_id=device.customer_id,
        device_type=device.device_type,
        status=DeviceStatus.ACTIVE,
        is_online=True,                         
        created_at=datetime.now(),      
        updated_at=datetime.now()
    )
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/{device.device_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    
    # Verify function was called
    mock_activate.assert_called_once()

@pytest.mark.asyncio
async def test_activate_device_no_permission(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer user attempting to activate a device (no permission)"""
    response = client.post(
        f"{settings.API_V1_STR}/devices/{device.device_id}/activate",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


# Test delete device endpoint (DELETE /devices/{device_id})
@pytest.mark.asyncio
@patch('app.utils.aws_iot.iot_core.delete_thing_certificate')
@patch('app.crud.device.device.cascade_delete')
@patch('app.crud.device.device.safe_delete_check')
async def test_delete_device(mock_safe_check, mock_cascade_delete, mock_delete_thing, client: TestClient, db: AsyncSession, admin_token: str, active_device: Device):
    """Test deleting a device with cascade delete"""
    # Configure mocks
    mock_delete_thing.return_value = True
    mock_safe_check.return_value = {
        'device_solutions': 1,
        'jobs': 2,
        'device_commands': 0,
        'human_data_records': 5,
        'traffic_data_records': 10
    }
    mock_cascade_delete.return_value = Device(
        device_id=active_device.device_id,
        name=active_device.name,
        customer_id=active_device.customer_id,
        device_type=active_device.device_type,
        status=DeviceStatus.DECOMMISSIONED,
        is_online=True,                         
        created_at=datetime.now(),      
        updated_at=datetime.now()
    )
    
    response = client.delete(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify functions were called
    mock_safe_check.assert_called_once()
    mock_cascade_delete.assert_called_once()
    mock_delete_thing.assert_called_once()

@pytest.mark.asyncio
async def test_delete_device_no_permission(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer user attempting to delete a device (no permission)"""
    response = client.delete(
        f"{settings.API_V1_STR}/devices/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

@pytest.mark.asyncio
async def test_delete_nonexistent_device(client: TestClient, admin_token: str):
    """Test deleting a non-existent device"""
    nonexistent_id = uuid.uuid4()
    response = client.delete(
        f"{settings.API_V1_STR}/devices/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]

@pytest.mark.asyncio
async def test_get_compatible_devices_for_solution_by_customer_all(client: TestClient, admin_token: str, customer: Customer, solution: Solution):
    """Test getting all devices compatible with a solution for a customer"""
    # First, get a solution from the database
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{solution.solution_id}/customer/{customer.customer_id}?available_only=false",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify that all returned devices belong to the customer and are compatible with the solution
    for device_item in data:
        assert str(device_item["customer_id"]) == str(customer.customer_id)
        # Verify device type is in solution's compatibility list
        assert device_item["device_type"] in solution.compatibility

@pytest.mark.asyncio
async def test_get_compatible_devices_for_solution_by_customer_available_only(client: TestClient, admin_token: str, customer: Customer, solution: Solution):
    """Test getting only available devices compatible with a solution for a customer"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{solution.solution_id}/customer/{customer.customer_id}?available_only=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Now use a separate API call to verify these devices don't have solutions deployed
    # This tests the endpoint's behavior rather than directly accessing the DB
    for device_item in data:
        device_id = device_item["device_id"]
        device_solutions_response = client.get(
            f"{settings.API_V1_STR}/device-solutions/device/{device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert device_solutions_response.status_code == 200
        device_solutions = device_solutions_response.json()
        assert len(device_solutions) == 0
    
@pytest.mark.asyncio
async def test_get_compatible_devices_for_solution_by_customer_as_customer_admin(client: TestClient, customer_admin_token: str, customer_admin_user: User, solution: Solution):
    """Test customer user getting devices compatible with a solution for their customer"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{solution.solution_id}/customer/{customer_admin_user.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All devices should belong to the user's customer
    for device_item in data:
        assert str(device_item["customer_id"]) == str(customer_admin_user.customer_id)


@pytest.mark.asyncio
async def test_get_compatible_devices_for_solution_by_customer_unauthorized(client: TestClient, customer_admin_token: str, suspended_customer: Customer, solution: Solution):
    """Test customer user attempting to get devices for a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{solution.solution_id}/customer/{suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]

@pytest.mark.asyncio
async def test_get_compatible_devices_nonexistent_solution(client: TestClient, admin_token: str, customer: Customer):
    """Test getting devices with non-existent solution"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{nonexistent_id}/customer/{customer.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Solution not found" in data["detail"]

@pytest.mark.asyncio
async def test_get_compatible_devices_nonexistent_customer(client: TestClient, admin_token: str, solution: Solution):
    """Test getting devices with non-existent customer"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/devices/compatible/solution/{solution.solution_id}/customer/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer not found" in data["detail"]

# =============================================================================
# Test cases for batch device status (POST /devices/batch-status)
# =============================================================================

@pytest.mark.asyncio
async def test_get_batch_device_status_admin(client: TestClient, admin_token: str, device: Device, active_device: Device, db: AsyncSession):
    """Test admin getting batch device status"""
    # Ensure we have a fresh database state
    await db.commit()
    
    batch_request = {
        "device_ids": [str(device.device_id), str(active_device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=batch_request
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert str(device.device_id) in data
    assert str(active_device.device_id) in data
    
    # Check device status structure
    device_status = data[str(device.device_id)]
    assert "device_id" in device_status
    assert "device_name" in device_status
    assert "is_online" in device_status
    assert device_status["device_name"] == device.name



@pytest.mark.asyncio
async def test_get_batch_device_status_customer_admin_own_devices(client: TestClient, customer_admin_token: str, device: Device, db: AsyncSession):
    """Test customer admin getting status for their own devices"""
    batch_request = {
        "device_ids": [str(device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=batch_request
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(device.device_id) in data
    device_status = data[str(device.device_id)]
    assert device_status["device_name"] == device.name
    assert "is_online" in device_status



@pytest.mark.asyncio
async def test_get_batch_device_status_mixed_valid_invalid_devices(client: TestClient, admin_token: str, device: Device, db: AsyncSession):
    """Test batch status with mix of valid and invalid device IDs"""
    invalid_device_id = str(uuid.uuid4())
    
    batch_request = {
        "device_ids": [str(device.device_id), invalid_device_id]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=batch_request
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Valid device should have normal status
    assert str(device.device_id) in data
    valid_status = data[str(device.device_id)]
    assert valid_status["device_name"] == device.name
    assert "error" not in valid_status or valid_status["error"] is None
    
    # Invalid device should have error
    assert invalid_device_id in data
    invalid_status = data[invalid_device_id]
    assert invalid_status["error"] == "Device not found"
    assert invalid_status["device_name"] == "Unknown"



@pytest.mark.asyncio
async def test_get_batch_device_status_empty_device_list(client: TestClient, admin_token: str, db: AsyncSession):
    """Test batch status with empty device list"""
    batch_request = {
        "device_ids": []
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=batch_request
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 0



@pytest.mark.asyncio
@patch('app.api.routes.devices.iot_command_service.get_device_shadow')
async def test_get_batch_device_status_with_shadow_data(
    mock_get_shadow, client: TestClient, admin_token: str, active_device: Device, db: AsyncSession
):
    """Test batch status with AWS IoT shadow data"""
    # Mock shadow response for online device
    mock_get_shadow.return_value = {
        "state": {
            "reported": {
                "applicationStatus": {
                    "status": "online",
                    "timestamp": "2025-01-01T00:00:00Z"
                }
            }
        }
    }
    
    batch_request = {
        "device_ids": [str(active_device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=batch_request
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    device_status = data[str(active_device.device_id)]
    assert device_status["is_online"] == True



@pytest.mark.asyncio
async def test_get_batch_device_status_unauthorized(client: TestClient, device: Device, db: AsyncSession):
    """Test batch status without authentication"""
    batch_request = {
        "device_ids": [str(device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/devices/batch-status",
        json=batch_request
    )
    
    # Check response - should be unauthorized
    assert response.status_code == 401


# =============================================================================
# Test cases for device image retrieval (GET /devices/{device_id}/image)
# =============================================================================

@pytest.mark.asyncio
@patch('app.api.routes.devices.boto3.client')
async def test_get_device_image_admin(mock_boto_client, client: TestClient, admin_token: str, active_device: Device):
    """Test admin getting device image"""
    # Mock S3 client and response
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    
    # Mock successful S3 response
    mock_response = {
        'Body': MagicMock(),
        'ContentType': 'image/jpeg'
    }
    mock_response['Body'].read.return_value = b'fake_image_data'
    mock_s3.get_object.return_value = mock_response
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "no-cache" in response.headers["cache-control"]
    assert response.content == b'fake_image_data'
    
    # Verify S3 call
    mock_s3.get_object.assert_called_once_with(
        Bucket="cc-captured-images",
        Key=f"captures/City Eye/{active_device.name}/capture.jpg"
    )


@pytest.mark.asyncio
@patch('app.api.routes.devices.boto3.client')
async def test_get_device_image_customer_admin_own_device(
    mock_boto_client, client: TestClient, customer_admin_token: str, active_device: Device
):
    """Test customer admin getting image for their own device"""
    # Mock S3 client
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    
    mock_response = {
        'Body': MagicMock(),
        'ContentType': 'image/jpeg'
    }
    mock_response['Body'].read.return_value = b'customer_device_image'
    mock_s3.get_object.return_value = mock_response
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.content == b'customer_device_image'


@pytest.mark.asyncio
@patch('app.crud.customer.customer.get_by_id')
@patch('app.utils.aws_iot.iot_core.provision_device')
async def test_get_device_image_customer_admin_unauthorized(
    mock_provision, mock_get_customer, client: TestClient, customer_admin_token: str, suspended_customer: Customer, admin_token: str
):
    """Test customer admin attempting to get image for device from different customer"""
    # Mock customer with IoT Thing Group for suspended customer
    customer_with_iot = MagicMock()
    customer_with_iot.customer_id = suspended_customer.customer_id
    customer_with_iot.iot_thing_group_name = "test-image-customer-group"
    mock_get_customer.return_value = customer_with_iot
    
    # Mock AWS IoT provisioning response
    mock_provision.return_value = {
        "thing_name": "D-IMG999",
        "thing_arn": "arn:aws:iot:region:account:thing/D-IMG999",
        "certificate_id": "test-img-cert-id",
        "certificate_arn": "arn:aws:iot:region:account:cert/test-img-cert-id",
        "certificate_path": "s3://bucket/certs/test-img-cert-id.pem",
        "private_key_path": "s3://bucket/keys/test-img-cert-id.key",
        "certificate_url": "https://s3.amazonaws.com/bucket/certs/test-img-cert-id.pem",
        "private_key_url": "https://s3.amazonaws.com/bucket/keys/test-img-cert-id.key"
    }
    
    # Create device for different customer
    device_data = {
        "description": "Device for different customer",
        "mac_address": "FF:EE:DD:CC:BB:AA",
        "serial_number": "SN888888888",
        "device_type": "NVIDIA_JETSON",
        "customer_id": str(suspended_customer.customer_id),
    }
    
    device_response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    assert device_response.status_code == 200
    other_device = device_response.json()
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{other_device['device_id']}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


@pytest.mark.asyncio
async def test_get_device_image_device_not_found(client: TestClient, admin_token: str):
    """Test getting image for non-existent device"""
    nonexistent_id = uuid.uuid4()
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{nonexistent_id}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Device not found" in data["detail"]


@pytest.mark.asyncio
@patch('app.crud.device.device.get_by_id')
async def test_get_device_image_device_inactive_mocked(mock_get_device, client: TestClient, admin_token: str, device: Device):
    """Test getting image for inactive device using mocked device status"""
    # Create a mock device with inactive status
    mock_inactive_device = MagicMock()
    mock_inactive_device.device_id = device.device_id
    mock_inactive_device.customer_id = device.customer_id
    mock_inactive_device.name = device.name
    mock_inactive_device.status = DeviceStatus.DECOMMISSIONED  # Device is not active
    
    mock_get_device.return_value = mock_inactive_device
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{device.device_id}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should fail because device is not active
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not active" in data["detail"]


@pytest.mark.asyncio
@patch('app.api.routes.devices.boto3.client')
async def test_get_device_image_aws_credentials_error(mock_boto_client, client: TestClient, admin_token: str, active_device: Device):
    """Test getting image when AWS credentials are not configured"""
    # Mock S3 client to raise NoCredentialsError
    mock_boto_client.side_effect = NoCredentialsError()
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/image?solution=City Eye",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be server error
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "credentials not configured" in data["detail"]


@pytest.mark.asyncio
async def test_get_device_image_unauthorized(client: TestClient, active_device: Device):
    """Test getting device image without authentication"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/image?solution=City Eye"
    )
    
    # Check response - should be unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_device_image_missing_solution_parameter(client: TestClient, admin_token: str, active_device: Device):
    """Test getting device image without solution parameter"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/image",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be validation error
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

# Test delete preview endpoint (GET /devices/{device_id}/delete-preview)
@pytest.mark.asyncio
@patch('app.crud.device.device.safe_delete_check')
async def test_preview_device_deletion(mock_safe_check, client: TestClient, admin_token: str, active_device: Device):
    """Test previewing device deletion to see related data counts"""
    # Mock the safe delete check response
    mock_safe_check.return_value = {
        'device_solutions': 2,
        'jobs': 5,
        'device_commands': 1,
        'human_data_records': 10,
        'traffic_data_records': 15
    }
    
    response = client.get(
        f"{settings.API_V1_STR}/devices/{active_device.device_id}/delete-preview",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data['device_solutions'] == 2
    assert data['jobs'] == 5
    assert data['device_commands'] == 1
    assert data['human_data_records'] == 10
    assert data['traffic_data_records'] == 15
    
    # Verify function was called
    mock_safe_check.assert_called_once()

@pytest.mark.asyncio
async def test_preview_device_deletion_no_permission(client: TestClient, customer_admin_token: str, device: Device):
    """Test customer user attempting to preview device deletion (no permission)"""
    response = client.get(
        f"{settings.API_V1_STR}/devices/{device.device_id}/delete-preview",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]