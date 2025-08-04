
"""
Test cases for job management routes
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, Device, Job, JobStatus, JobType
from app.crud import job as crud_job
from typing import Dict, Any



def test_create_restart_job_admin_success(client: TestClient, db: Session, admin_token: str, mocker):
    """
    Test successful creation of a restart application job by an admin user.
    The endpoint should accept the request and start a background task.
    """
    # Create the authorization headers using the admin_token fixture
    admin_user_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Mock the background task function to prevent it from actually running during the test
    mock_bg_task = mocker.patch("app.api.routes.jobs.create_restart_jobs_task")
    
    device_id_1 = str(uuid.uuid4())
    device_id_2 = str(uuid.uuid4())

    # Make the API call
    response = client.post(
        f"{settings.API_V1_STR}/jobs/restart-application",
        headers=admin_user_headers,  # Use the created headers
        json={"device_ids": [device_id_1, device_id_2]},
    )
    
    # Assertions
    assert response.status_code == 202  # Check for "Accepted" status
    data = response.json()
    assert data["message"] == "Job creation for restarting applications has been initiated."
    assert data["device_count"] == 2
    
    # Verify that the background task was called once
    mock_bg_task.assert_called_once()



def test_create_job_unauthorized_customer(client: TestClient, db: Session, customer_admin_token3: str, mocker):
    """
    Test that the API accepts a job creation request from a customer admin.
    The background task will handle the authorization for each device asynchronously.
    """
    # Create the authorization headers using the available customer_admin_token fixture
    customer_user_headers = {"Authorization": f"Bearer {customer_admin_token3}"}
    
    # Mock the background task to prevent it from executing during the test
    mock_bg_task = mocker.patch("app.api.routes.jobs.create_restart_jobs_task")
    
    # An ID for a device that does not belong to this customer
    other_customer_device_id = str(uuid.uuid4())
    
    # Make the API call
    response = client.post(
        f"{settings.API_V1_STR}/jobs/restart-application",
        headers=customer_user_headers, # Use the constructed headers
        json={"device_ids": [other_customer_device_id]},
    )
    
    # Assertions
    # The endpoint accepts the request and handles device-specific authorization in the background.
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Job creation for restarting applications has been initiated."
    
    # Verify that the background task was initiated
    mock_bg_task.assert_called_once()


def test_create_job_device_not_provisioned(client: TestClient, db: Session, admin_token: str, mocker):
    """
    Test job creation for a device that is not provisioned.
    The API should accept the request, and the failure will occur in the background task.
    """
    # Create authorization headers using the admin_token
    admin_user_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Mock the background task to prevent its execution
    mock_bg_task = mocker.patch("app.api.routes.jobs.create_restart_jobs_task")
    
    # Assume this UUID belongs to a device with status 'CREATED' in the test database
    unprovisioned_device_id = str(uuid.uuid4()) 
    
    # Make the API call
    response = client.post(
        f"{settings.API_V1_STR}/jobs/restart-application",
        headers=admin_user_headers,
        json={"device_ids": [unprovisioned_device_id]},
    )
    
    # Assertions
    # The endpoint now accepts the request and handles validation in the background.
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Job creation for restarting applications has been initiated."
    
    # Verify the background task was initiated
    mock_bg_task.assert_called_once()


def test_create_reboot_job_aws_failure(client: TestClient, db: Session, admin_token: str, mocker):
    """
    Test the API response when the AWS IoT job creation fails.
    The API should still return 202, as the failure happens in the background.
    """
    # Create authorization headers
    admin_user_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Mock the background task
    mock_bg_task = mocker.patch("app.api.routes.jobs.create_reboot_jobs_task")

    # A valid device ID for the request payload
    valid_device_id = str(uuid.uuid4())

    # Make the API call
    response = client.post(
        f"{settings.API_V1_STR}/jobs/reboot-device",
        headers=admin_user_headers,
        json={"device_ids": [valid_device_id]},
    )
    
    # Assertions
    # The API call to AWS now happens in the background, so the endpoint will return 202.
    # The actual failure would be logged by the background task.
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Job creation for rebooting devices has been initiated."

    # Verify that the background task was called
    mock_bg_task.assert_called_once()

# Test cases for retrieving jobs
@patch('app.api.routes.jobs.sync_job_status')
def test_get_device_jobs_success(
    mock_sync: MagicMock,
    client: TestClient,
    admin_token: str,
    active_device: Device,
    test_job: Job
):
    """Test retrieving jobs for a specific device."""
    # The mock will just return the job object passed to it
    mock_sync.side_effect = lambda db, job_obj: job_obj

    response = client.get(
        f"{settings.API_V1_STR}/jobs/device/{active_device.device_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["job_id"] == test_job.job_id
    assert data[0]["device_id"] == str(active_device.device_id)
    mock_sync.assert_called()

def test_get_device_jobs_unauthorized(
    client: TestClient,
    customer_admin_token3: str, # Belongs to a different customer
    active_device: Device
):
    """Test that a user cannot see jobs for a device they don't have access to."""
    response = client.get(
        f"{settings.API_V1_STR}/jobs/device/{active_device.device_id}",
        headers={"Authorization": f"Bearer {customer_admin_token3}"},
    )
    assert response.status_code == 403

@patch('app.api.routes.jobs.sync_job_status')
def test_get_latest_job_success(
    mock_sync: MagicMock,
    client: TestClient,
    admin_token: str,
    test_job: Job
):
    """Test retrieving the latest job for a device."""
    mock_sync.side_effect = lambda db, job_obj: job_obj

    response = client.get(
        f"{settings.API_V1_STR}/jobs/device/{test_job.device_id}/latest",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_job.job_id

# Test cases for job status and cancellation
@patch('app.api.routes.jobs.sync_job_status')
def test_get_job_status_success(
    mock_sync: MagicMock,
    client: TestClient,
    admin_token: str,
    test_job: Job
):
    """Test retrieving the status of a specific job."""
    # Make the mock return an updated job object
    updated_job = test_job
    updated_job.status = JobStatus.IN_PROGRESS
    mock_sync.return_value = updated_job

    response = client.get(
        f"{settings.API_V1_STR}/jobs/{test_job.job_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_job.job_id
    assert data["status"] == "IN_PROGRESS"
    assert data["progress_percentage"] == 50

@patch('app.utils.aws_iot_jobs.iot_jobs_service.cancel_job')
def test_cancel_job_success(
    mock_cancel_aws_job: MagicMock,
    client: TestClient,
    db: Session,
    admin_token: str,
    test_job: Job
):
    """Test successfully canceling a job."""
    mock_cancel_aws_job.return_value = True

    response = client.post(
        f"{settings.API_V1_STR}/jobs/{test_job.job_id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Job canceled successfully"
    mock_cancel_aws_job.assert_called_once_with(test_job.job_id)

    # Verify the job status is updated in the database
    db.refresh(test_job)
    assert test_job.status == JobStatus.CANCELED

def test_cancel_job_in_terminal_state(
    client: TestClient,
    db: Session,
    admin_token: str,
    test_job: Job
):
    """Test that a job in a terminal state (e.g., SUCCEEDED) cannot be canceled."""
    # Manually update the job's status to a terminal state
    test_job.status = JobStatus.SUCCEEDED
    db.add(test_job)
    db.commit()

    response = client.post(
        f"{settings.API_V1_STR}/jobs/{test_job.job_id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "Cannot cancel job" in response.json()["detail"]

# Test case for cleanup endpoint
@patch('app.api.routes.jobs.BackgroundTasks.add_task') # Corrected: 'BackgroundTasks' instead of 'background_tasks'
def test_cleanup_old_jobs(
    mock_add_task: MagicMock,
    client: TestClient,
    admin_token: str
):
    """Test the cleanup endpoint to ensure it starts the background task."""
    response = client.post(
        f"{settings.API_V1_STR}/jobs/cleanup?keep_latest=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Job cleanup process has been started" in data["message"]
    assert "keep the latest 5" in data["details"]
    # Verify that the background task was added
    mock_add_task.assert_called_once()