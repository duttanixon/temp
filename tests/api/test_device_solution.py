"""
Test cases for device solution management routes
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.device_solution import DeviceSolution, DeviceSolutionStatus
from app.models.device import Device, DeviceStatus
from app.models.solution import Solution
from app.models.customer_solution import CustomerSolution
from app.models.user import User
from app.core.config import settings
from datetime import datetime

@patch('app.crud.device.device.get_by_id')
def test_deploy_solution_to_nonexistent_device(
    mock_get_device, client: TestClient, admin_token: str
):
    """Test deploying a solution to a non-existent device"""
    # Mock that device doesn't exist
    mock_get_device.return_value = None
    
    solution_data = {
        "device_id": str(uuid.uuid4()),  # Random ID
        "solution_id": str(uuid.uuid4()),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
def test_deploy_solution_to_device_no_access(
    mock_get_solution, mock_get_device,
    client: TestClient, customer_user_token: str,
    device: Device
):
    """Test customer user deploying a solution to a device they don't own"""
    # Create a device with a different customer
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = uuid.uuid4()  # Different customer
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.compatibility = [device.device_type.value]
    mock_get_solution.return_value = mock_solution
    
    solution_data = {
        "device_id": str(device.device_id),
        "solution_id": str(mock_solution.solution_id),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=solution_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
@patch('app.crud.customer_solution.customer_solution.check_customer_has_access')
def test_deploy_solution_customer_no_access(
    mock_check_access, mock_get_solution, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test deploying a solution that the customer doesn't have access to"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.compatibility = [device.device_type.value]
    mock_get_solution.return_value = mock_solution
    
    # Mock access check - no access
    mock_check_access.return_value = False
    
    solution_data = {
        "device_id": str(device.device_id),
        "solution_id": str(mock_solution.solution_id),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "does not have access" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
@patch('app.crud.customer_solution.customer_solution.check_customer_has_access')
def test_deploy_incompatible_solution(
    mock_check_access, mock_get_solution, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test deploying an incompatible solution to a device"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.name = "Incompatible Solution"
    mock_solution.compatibility = ["SOME_OTHER_TYPE"]  # Not compatible with device
    mock_get_solution.return_value = mock_solution
    
    # Mock access check
    mock_check_access.return_value = True
    
    solution_data = {
        "device_id": str(device.device_id),
        "solution_id": str(mock_solution.solution_id),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should be bad request
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not compatible" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
@patch('app.crud.customer_solution.customer_solution.check_customer_has_access')
@patch('app.crud.device_solution.device_solution.get_by_device_and_solution')
def test_deploy_already_deployed_solution(
    mock_get_by_device_and_solution, mock_check_access, 
    mock_get_solution, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test deploying a solution that's already deployed to the device"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.name = "Test Solution"
    mock_solution.compatibility = [device.device_type.value]
    mock_get_solution.return_value = mock_solution
    
    # Mock access check
    mock_check_access.return_value = True
    
    # Mock that solution is already deployed
    mock_deployment = MagicMock()
    mock_deployment.id = uuid.uuid4()
    mock_get_by_device_and_solution.return_value = mock_deployment
    
    solution_data = {
        "device_id": str(device.device_id),
        "solution_id": str(mock_solution.solution_id),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should be bad request
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already deployed" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
@patch('app.crud.customer_solution.customer_solution.check_customer_has_access')
@patch('app.crud.device_solution.device_solution.get_by_device_and_solution')
@patch('app.crud.device_solution.device_solution.get_by_device')
def test_deploy_another_solution_already_deployed(
    mock_get_by_device, mock_get_by_device_and_solution, 
    mock_check_access, mock_get_solution, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test deploying a solution when another solution is already deployed"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.name = "Test Solution"
    mock_solution.compatibility = [device.device_type.value]
    mock_get_solution.return_value = mock_solution
    
    # Mock access check
    mock_check_access.return_value = True
    
    # Mock that this specific solution is not deployed
    mock_get_by_device_and_solution.return_value = None
    
    # But another solution is already deployed
    mock_other_deployment = MagicMock()
    mock_other_deployment.solution_id = uuid.uuid4()  # Different solution
    mock_get_by_device.return_value = [mock_other_deployment]
    
    # Create another solution for the error message
    mock_other_solution = MagicMock()
    mock_other_solution.name = "Other Solution"
    
    # Mock that solution.get_by_id will return this other solution
    with patch('app.crud.solution.solution.get_by_id', side_effect=lambda db, solution_id: 
               mock_other_solution if solution_id == mock_other_deployment.solution_id else mock_solution):
        
        solution_data = {
            "device_id": str(device.device_id),
            "solution_id": str(mock_solution.solution_id),
            "status": "PROVISIONING",
            "version_deployed": "1.0.0"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/device-solutions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=solution_data
        )
        
        # Check response - should be bad request
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already has solution" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.solution.solution.get_by_id')
@patch('app.crud.customer_solution.customer_solution.check_customer_has_access')
@patch('app.crud.device_solution.device_solution.get_by_device_and_solution')
@patch('app.crud.device_solution.device_solution.get_by_device')
@patch('app.crud.customer_solution.customer_solution.count_deployed_devices')
@patch('app.crud.customer_solution.customer_solution.get_by_customer_and_solution')
def test_deploy_solution_license_limit_reached(
    mock_get_customer_solution, mock_count_deployed_devices,
    mock_get_by_device, mock_get_by_device_and_solution,
    mock_check_access, mock_get_solution, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test deploying a solution when license limit is reached"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_device.device_type = device.device_type
    mock_get_device.return_value = mock_device
    
    # Mock solution
    mock_solution = MagicMock()
    mock_solution.solution_id = uuid.uuid4()
    mock_solution.name = "Test Solution"
    mock_solution.compatibility = [device.device_type.value]
    mock_get_solution.return_value = mock_solution
    
    # Mock access check
    mock_check_access.return_value = True
    
    # Mock that solution is not already deployed
    mock_get_by_device_and_solution.return_value = None
    mock_get_by_device.return_value = []
    
    # Mock customer solution license
    mock_customer_solution = MagicMock()
    mock_customer_solution.max_devices = 5
    mock_get_customer_solution.return_value = mock_customer_solution
    
    # Mock that license limit is reached (count = max)
    mock_count_deployed_devices.return_value = 5
    
    solution_data = {
        "device_id": str(device.device_id),
        "solution_id": str(mock_solution.solution_id),
        "status": "PROVISIONING",
        "version_deployed": "1.0.0"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/device-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=solution_data
    )
    
    # Check response - should be bad request
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "reached maximum" in data["detail"]

# Test getting device solutions (GET /device-solutions/device/{device_id})
@patch('app.crud.device.device.get_by_id')
@patch('app.crud.device_solution.device_solution.get_by_device')
@patch('app.crud.solution.solution.get_by_id')
def test_get_device_solutions(
    mock_get_solution, mock_get_by_device, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test getting solutions deployed to a device"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_get_device.return_value = mock_device
    
    # Mock deployed solution with all required fields for DeviceSolutionDetailView
    solution_id = uuid.uuid4()
    deployment_id = uuid.uuid4()
    
    mock_deployment = MagicMock()
    mock_deployment.id = deployment_id
    mock_deployment.device_id = device.device_id
    mock_deployment.solution_id = solution_id
    mock_deployment.status = "ACTIVE"
    mock_deployment.configuration = {"param1": "value1"}
    mock_deployment.version_deployed = "1.0.0"
    mock_deployment.metrics = None
    mock_deployment.last_update = datetime.now()
    mock_deployment.created_at = datetime.now()
    mock_deployment.updated_at = datetime.now()
    
    # The __dict__ approach wasn't working because it needs all required fields
    # Use side_effect to have the function return the complete dictionary
    def solution_dict_side_effect():
        return {
            "id": deployment_id,
            "device_id": device.device_id,
            "solution_id": solution_id,
            "status": "ACTIVE",
            "configuration": {"param1": "value1"},
            "version_deployed": "1.0.0",
            "metrics": None,
            "last_update": mock_deployment.last_update,
            "created_at": mock_deployment.created_at,
            "updated_at": mock_deployment.updated_at,
            "solution_name": "Test Solution",
            "solution_description": "A test solution"
        }
    
    # Mock the solution service to return the dictionary
    mock_get_by_device.return_value = [mock_deployment]
    
    # Mock solution details
    mock_solution = MagicMock()
    mock_solution.name = "Test Solution"
    mock_solution.description = "A test solution"
    mock_get_solution.return_value = mock_solution
    
    # Patch the function that combines device_solution and solution info
    with patch('app.api.routes.device_solutions.device_solution.get_by_device', return_value=[mock_deployment]), \
         patch('app.api.routes.device_solutions.solution.get_by_id', return_value=mock_solution):
        
        response = client.get(
            f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "solution_name" in data[0]
    assert data[0]["solution_name"] == "Test Solution"
    assert "solution_description" in data[0]
    assert data[0]["solution_description"] == "A test solution"



@patch('app.crud.device.device.get_by_id')
def test_get_device_solutions_nonexistent_device(
    mock_get_device, client: TestClient, admin_token: str
):
    """Test getting solutions for a non-existent device"""
    # Mock that device doesn't exist
    mock_get_device.return_value = None
    
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/device/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.crud.device.device.get_by_id')
def test_get_device_solutions_no_authorization(
    mock_get_device, client: TestClient, customer_user_token: str, device: Device
):
    """Test customer user getting solutions for a device they don't own"""
    # Create a device with a different customer
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = uuid.uuid4()  # Different customer
    mock_get_device.return_value = mock_device
    
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


@patch('app.crud.device.device.get_by_id')
def test_update_device_solution_nonexistent_device(
    mock_get_device, client: TestClient, admin_token: str
):
    """Test updating a solution for a non-existent device"""
    # Mock that device doesn't exist
    mock_get_device.return_value = None
    
    nonexistent_id = uuid.uuid4()
    update_data = {
        "status": "ACTIVE",
        "version_deployed": "1.1.0"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/device-solutions/device/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.crud.device.device.get_by_id')
def test_update_device_solution_no_authorization(
    mock_get_device, client: TestClient, customer_user_token: str, device: Device
):
    """Test customer user updating a solution for a device they don't own"""
    # Create a device with a different customer
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = uuid.uuid4()  # Different customer
    mock_get_device.return_value = mock_device
    
    update_data = {
        "status": "ACTIVE",
        "version_deployed": "1.1.0"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.device_solution.device_solution.get_by_device')
def test_update_device_solution_no_solution_deployed(
    mock_get_by_device, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test updating a solution when no solution is deployed"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_get_device.return_value = mock_device
    
    # Mock that no solution is deployed
    mock_get_by_device.return_value = []
    
    update_data = {
        "status": "ACTIVE",
        "version_deployed": "1.1.0"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "No solution deployed" in data["detail"]



@patch('app.crud.device.device.get_by_id')
def test_remove_solution_nonexistent_device(
    mock_get_device, client: TestClient, admin_token: str
):
    """Test removing a solution from a non-existent device"""
    # Mock that device doesn't exist
    mock_get_device.return_value = None
    
    nonexistent_id = uuid.uuid4()
    response = client.delete(
        f"{settings.API_V1_STR}/device-solutions/device/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.device_solution.device_solution.get_by_device')
def test_remove_solution_no_solution_deployed(
    mock_get_by_device, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test removing a solution when no solution is deployed"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_get_device.return_value = mock_device
    
    # Mock that no solution is deployed
    mock_get_by_device.return_value = []
    
    response = client.delete(
        f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "No solution deployed" in data["detail"]


def test_remove_solution_customer_user(
    client: TestClient, customer_user_token: str, device: Device
):
    """Test customer user attempting to remove a solution (no permission)"""
    response = client.delete(
        f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]



# Test getting current device solution (GET /device-solutions/current/device/{device_id})
@patch('app.crud.device.device.get_by_id')
@patch('app.crud.device_solution.device_solution.get_by_device')
@patch('app.crud.solution.solution.get_by_id')
def test_get_current_device_solution(
    mock_get_solution, mock_get_by_device, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test getting current solution for a device"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_get_device.return_value = mock_device
    
    # Mock deployed solution
    mock_deployment = MagicMock()
    mock_deployment.id = uuid.uuid4()
    mock_deployment.device_id = device.device_id
    mock_deployment.solution_id = uuid.uuid4()
    mock_deployment.status = "ACTIVE"
    mock_deployment.configuration = {"param1": "value1"}
    mock_deployment.version_deployed = "1.0.0"
    mock_deployment.last_update = datetime.now()
    mock_deployment.created_at = datetime.now()
    mock_deployment.updated_at = datetime.now()
    mock_get_by_device.return_value = [mock_deployment]
    
    # Mock solution details
    mock_solution = MagicMock()
    mock_solution.name = "Test Solution"
    mock_solution.description = "A test solution"
    mock_get_solution.return_value = mock_solution
    
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/current/device/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert str(data["id"]) == str(mock_deployment.id)
    assert str(data["device_id"]) == str(device.device_id)
    assert str(data["solution_id"]) == str(mock_deployment.solution_id)
    assert data["solution_name"] == mock_solution.name
    assert data["solution_description"] == mock_solution.description
    assert data["status"] == "ACTIVE"
    assert data["version_deployed"] == "1.0.0"

@patch('app.crud.device.device.get_by_id')
def test_get_current_device_solution_nonexistent_device(
    mock_get_device, client: TestClient, admin_token: str
):
    """Test getting current solution for a non-existent device"""
    # Mock that device doesn't exist
    mock_get_device.return_value = None
    
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/current/device/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


@patch('app.crud.device.device.get_by_id')
def test_get_current_device_solution_no_authorization(
    mock_get_device, client: TestClient, customer_user_token: str, device: Device
):
    """Test customer user getting current solution for a device they don't own"""
    # Create a device with a different customer
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = uuid.uuid4()  # Different customer
    mock_get_device.return_value = mock_device
    
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/current/device/{device.device_id}",
        headers={"Authorization": f"Bearer {customer_user_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"]


@patch('app.crud.device.device.get_by_id')
@patch('app.crud.device_solution.device_solution.get_by_device')
def test_get_current_device_solution_none_deployed(
    mock_get_by_device, mock_get_device,
    client: TestClient, admin_token: str, device: Device
):
    """Test getting current solution when no solution is deployed"""
    # Mock device
    mock_device = MagicMock()
    mock_device.device_id = device.device_id
    mock_device.customer_id = device.customer_id
    mock_get_device.return_value = mock_device
    
    # Mock that no solution is deployed
    mock_get_by_device.return_value = []
    
    response = client.get(
        f"{settings.API_V1_STR}/device-solutions/current/device/{device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be null
    assert response.status_code == 200
    assert response.json() is None

# # Test removing solution from device (DELETE /device-solutions/device/{device_id})
# @patch('app.crud.device.device.get_by_id')
# @patch('app.crud.device_solution.device_solution.get_by_device')
# @patch('app.crud.solution.solution.get_by_id')
# @patch('app.crud.device_solution.device_solution.remove')
# def test_remove_solution_from_device(
#     mock_remove, mock_get_solution, mock_get_by_device, mock_get_device,
#     client: TestClient, admin_token: str, device: Device
# ):
#     """Test removing a solution from a device"""
#     # Mock device
#     mock_device = MagicMock()
#     mock_device.device_id = device.device_id
#     mock_device.customer_id = device.customer_id
#     mock_device.name = device.name
#     mock_get_device.return_value = mock_device
    
#     # Mock deployed solution
#     mock_deployment = MagicMock()
#     mock_deployment.id = uuid.uuid4()
#     mock_deployment.solution_id = uuid.uuid4()
#     mock_get_by_device.return_value = [mock_deployment]
    
#     # Mock solution
#     mock_solution = MagicMock()
#     mock_solution.solution_id = mock_deployment.solution_id
#     mock_solution.name = "Test Solution"
#     mock_get_solution.return_value = mock_solution
    
#     # Mock removed deployment
#     mock_removed = MagicMock()
#     mock_removed.id = mock_deployment.id
#     mock_removed.device_id = device.device_id
#     mock_removed.solution_id = mock_deployment.solution_id
#     mock_remove.return_value = mock_removed
    
#     response = client.delete(
#         f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
#         headers={"Authorization": f"Bearer {admin_token}"}
#     )
    
#     # Check response
#     assert response.status_code == 200
#     data = response.json()
#     assert str(data["id"]) == str(mock_deployment.id)
#     assert str(data["device_id"]) == str(device.device_id)
#     assert str(data["solution_id"]) == str(mock_deployment.solution_id)
    
#     # Verify functions were called
#     mock_get_device.assert_called_once()
#     mock_get_by_device.assert_called_once()
#     mock_get_solution.assert_called_once()
#     mock_remove.assert_called_once()



# # Test updating device solution (PUT /device-solutions/device/{device_id})
# @patch('app.crud.device.device.get_by_id')
# @patch('app.crud.device_solution.device_solution.get_by_device')
# @patch('app.crud.device_solution.device_solution.update')
# @patch('app.crud.solution.solution.get_by_id')
# def test_update_device_solution(
#     mock_get_solution, mock_update, mock_get_by_device, mock_get_device,
#     client: TestClient, admin_token: str, device: Device
# ):
#     """Test updating a solution deployment by device ID"""
#     # Mock device
#     mock_device = MagicMock()
#     mock_device.device_id = device.device_id
#     mock_device.customer_id = device.customer_id
#     mock_get_device.return_value = mock_device
    
#     # Mock deployed solution
#     mock_deployment = MagicMock()
#     mock_deployment.id = uuid.uuid4()
#     mock_deployment.solution_id = uuid.uuid4()
#     mock_deployment.__dict__ = {
#         "id": mock_deployment.id,
#         "solution_id": mock_deployment.solution_id,
#         "status": "ACTIVE",
#         "version_deployed": "1.0.0"
#     }
#     mock_get_by_device.return_value = [mock_deployment]
    
#     # Mock updated deployment
#     mock_updated = MagicMock()
#     mock_updated.id = mock_deployment.id
#     mock_updated.solution_id = mock_deployment.solution_id
#     mock_updated.status = "ACTIVE"
#     mock_updated.version_deployed = "1.1.0"
#     mock_updated.configuration = {"param1": "new_value"}
#     mock_updated.__dict__ = {
#         "id": mock_updated.id,
#         "solution_id": mock_updated.solution_id,
#         "status": mock_updated.status,
#         "version_deployed": mock_updated.version_deployed,
#         "configuration": mock_updated.configuration
#     }
#     mock_update.return_value = mock_updated
    
#     # Mock solution details
#     mock_solution = MagicMock()
#     mock_solution.name = "Test Solution"
#     mock_solution.description = "A test solution"
#     mock_get_solution.return_value = mock_solution
    
#     update_data = {
#         "status": "ACTIVE",
#         "version_deployed": "1.1.0",
#         "configuration": {"param1": "new_value"}
#     }
    
#     response = client.put(
#         f"{settings.API_V1_STR}/device-solutions/device/{device.device_id}",
#         headers={"Authorization": f"Bearer {admin_token}"},
#         json=update_data
#     )
    
#     # Check response
#     assert response.status_code == 200
#     data = response.json()
#     assert str(data["id"]) == str(mock_deployment.id)
#     assert str(data["solution_id"]) == str(mock_deployment.solution_id)
#     assert data["version_deployed"] == "1.1.0"
#     assert data["configuration"] == {"param1": "new_value"}
#     assert data["solution_name"] == mock_solution.name
    
#     # Verify functions were called
#     mock_get_device.assert_called_once()
#     mock_get_by_device.assert_called_once()
#     mock_update.assert_called_once()
#     mock_get_solution.assert_called_once()
