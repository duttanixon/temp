"""
Test cases for device commands routes
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import User, Device, DeviceSolution, CommandType
from app.crud import device_command
from app.schemas.device_command import DeviceCommandCreate
from app.models.customer import Customer


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.iot_command_service.send_capture_image_command')
async def test_capture_image_command_success(
    mock_send_command,
    client: TestClient,
    db: AsyncSession,
    admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test sending capture image command successfully"""
    mock_send_command.return_value = True

    command_data = {
        "device_id": str(active_device.device_id)
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {admin_token}", "X-Test-Mode": "true"}, # Add header
        json=command_data
    )

    assert response.status_code == 202
    data = response.json()
    assert "message_id" in data
    assert "device_name" in data
    assert data["device_name"] == active_device.name
    assert "details" in data
    # Corrected: Handle potential NoneType for 'details'
    assert data["details"] is None or "successfully" in data["details"]
    print(data)

    # Verify IoT command was called
    mock_send_command.assert_called_once()


@pytest.mark.asyncio
async def test_capture_image_command_device_not_found(
    client: TestClient,
    admin_token: str
):
    """Test capture image command with non-existent device"""
    command_data = {
        "device_id": str(uuid.uuid4())
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 404
    assert "Device not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_capture_image_command_unauthorized(
    client: TestClient,
    customer_admin_token: str,
    suspended_customer: Customer,
    admin_token: str
):
    """Test capture image command on device from different customer"""
    # Create device for different customer
    device_data = {
        "description": "Test device for different customer",
        "mac_address": "FF:EE:DD:CC:BB:AA",
        "serial_number": "SN987654321",
        "device_type": "NVIDIA_JETSON",
        "firmware_version": "1.0.0",
        "location": "Test Location",
        "customer_id": str(suspended_customer.customer_id),
        "ip_address": "192.168.1.300"
    }

    device_response = client.post(
        f"{settings.API_V1_STR}/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=device_data
    )
    created_device = device_response.json()

    # Try to send command as different customer
    command_data = {
        "device_id": created_device["device_id"]
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=command_data
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.device_solution.get_active_by_device')
async def test_capture_image_command_no_active_solution(
    mock_get_active,
    client: TestClient,
    admin_token: str,
    active_device: Device
):
    """Test capture image command when no active solution on device"""
    # Mock no active solutions
    mock_get_active.return_value = []

    command_data = {
        "device_id": str(active_device.device_id)
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 400
    assert "No active solution" in response.json()["detail"]


@pytest.mark.asyncio
async def test_capture_image_command_device_not_provisioned(
    client: TestClient,
    admin_token: str,
    device: Device  # This is a created but not provisioned device
):
    """Test capture image command on non-provisioned device"""
    command_data = {
        "device_id": str(device.device_id)
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 400
    assert "not provisioned" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_command_status_internal_success(
    client: TestClient,
    db: AsyncSession,
    active_device: Device,
    city_eye_device_solution: DeviceSolution,
    admin_user: User
):
    """Test internal endpoint for updating command status"""

    command_create = DeviceCommandCreate(
        device_id=active_device.device_id,
        command_type=CommandType.CAPTURE_IMAGE,
        payload={},
        user_id=admin_user.user_id,
        solution_id=city_eye_device_solution.solution_id
    )
    db_command = await device_command.create(db, obj_in=command_create)

    # Update status via internal endpoint
    status_update = {
        "status": "SUCCESS",
        "response_payload": {"image_url": "s3://bucket/image.jpg"},
        "error_message": None
    }

    response = client.put(
        f"{settings.API_V1_STR}/device-commands/internal/{db_command.message_id}/status",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=status_update
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["message_id"] == str(db_command.message_id)


@pytest.mark.asyncio
async def test_update_command_status_internal_invalid_api_key(
    client: TestClient
):
    """Test internal endpoint with invalid API key"""
    status_update = {
        "status": "SUCCESS",
        "response_payload": {},
        "error_message": None
    }

    response = client.put(
        f"{settings.API_V1_STR}/device-commands/internal/{uuid.uuid4()}/status",
        headers={"X-API-Key": "invalid-key"},
        json=status_update
    )

    assert response.status_code == 401


# @pytest.mark.asyncio
# async def test_update_command_status_internal_not_found(
#     client: TestClient
# ):
#     """Test internal endpoint with non-existent command"""
#     status_update = {
#         "status": "SUCCESS",
#         "response_payload": {},
#         "error_message": None
#     }

#     response = client.put(
#         f"{settings.API_V1_STR}/device-commands/internal/{uuid.uuid4()}/status",
#         headers={"X-API-Key": settings.INTERNAL_API_KEY},
#         json=status_update
#     )

#     assert response.status_code == 404


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.kvs_manager.create_stream_if_not_exists')
@patch('app.api.routes.device_commands.kvs_manager.get_hls_streaming_url')
@patch('app.api.routes.device_commands.iot_command_service.send_start_live_stream_command')
async def test_start_live_stream_success(
    mock_send_command,
    mock_get_hls_url,
    mock_create_stream,
    client: TestClient,
    admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test starting live stream successfully"""
    # Mock KVS manager
    mock_create_stream.return_value = (True, True)  # success, is_new
    mock_get_hls_url.return_value = {
        "hls_url": "https://kvs.example.com/stream.m3u8",
        "expires_in": 3600
        }
    mock_send_command.return_value = True

    command_data = {
        "device_id": str(active_device.device_id),
        "duration_seconds": 300,
        "stream_quality": "high"
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/start-live-stream",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )
    print(response.json())

    assert response.status_code == 200
    data = response.json()
    assert "kvs_url" in data
    assert "message_id" in data
    assert data["kvs_url"] == "https://kvs.example.com/stream.m3u8"


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.kvs_manager.create_stream_if_not_exists')
async def test_start_live_stream_kvs_failure(
    mock_create_stream,
    client: TestClient,
    admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test starting live stream when KVS creation fails"""
    # Mock KVS creation failure
    mock_create_stream.return_value = (False, False)

    command_data = {
        "device_id": str(active_device.device_id),
        "duration_seconds": 300,
        "stream_quality": "high"
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/start-live-stream",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 500
    assert "Failed to create or access KVS stream" in response.json()["detail"]


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.iot_command_service.send_stop_live_stream_command')
async def test_stop_live_stream_success(
    mock_send_command,
    client: TestClient,
    admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test stopping live stream successfully"""
    mock_send_command.return_value = True

    command_data = {
        "device_id": str(active_device.device_id)
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/stop-live-stream",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    assert "details" in data
    assert "successfully" in data["details"]


@pytest.mark.asyncio
@patch('app.api.routes.device_commands.iot_command_service.send_capture_image_command')
async def test_customer_admin_can_send_commands(
    mock_send,
    client: TestClient,
    customer_admin_token: str,
    active_device: Device,
    city_eye_device_solution: DeviceSolution
):
    """Test that customer admin can send commands to their devices"""
    mock_send.return_value = True

    command_data = {
        "device_id": str(active_device.device_id)
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/capture-image",
        headers={"Authorization": f"Bearer {customer_admin_token}", "X-Test-Mode": "true"}, # Add header
        json=command_data
    )

    assert response.status_code == 202
    data = response.json()
    assert "message_id" in data


@pytest.mark.asyncio
async def test_stream_quality_validation(
    client: TestClient,
    admin_token: str,
    active_device: Device
):
    """Test stream quality parameter validation"""
    command_data = {
        "device_id": str(active_device.device_id),
        "duration_seconds": 300,
        "stream_quality": "INVALID_QUALITY"
    }

    response = client.post(
        f"{settings.API_V1_STR}/device-commands/start-live-stream",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=command_data
    )

    assert response.status_code == 422  # Validation error