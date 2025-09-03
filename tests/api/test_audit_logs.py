"""
Test cases for audit log routes
"""
import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import User, AuditLog, Customer
from app.schemas.audit import AuditLogActionType, AuditLogResourceType
from app.utils.audit import log_action

# Test cases for GET /audit-logs endpoint
@pytest.mark.asyncio
async def test_get_audit_logs_admin(client: TestClient, admin_token: str, db: AsyncSession, admin_user: User):
    """Test admin getting all audit logs"""
    # First, create a dummy log to ensure there's at least one log entry
    await log_action(
        db=db,
        user_id=admin_user.user_id,
        action_type=AuditLogActionType.LOGIN,
        resource_type=AuditLogResourceType.USER,
        resource_id=str(admin_user.user_id)
    )

    response = client.get(
        f"{settings.API_V1_STR}/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data
    assert data["total"] > 0

@pytest.mark.asyncio
async def test_get_audit_logs_engineer(client: TestClient, engineer_token: str):
    """Test engineer getting all audit logs"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data

@pytest.mark.asyncio
async def test_get_audit_logs_customer_admin(client: TestClient, customer_admin_token: str, customer_admin_user: User, db: AsyncSession):
    """Test customer admin getting logs for their organization"""
    await log_action(
        db=db,
        user_id=customer_admin_user.user_id,
        action_type=AuditLogActionType.LOGIN,
        resource_type=AuditLogResourceType.USER,
        resource_id=str(customer_admin_user.user_id)
    )
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    # Verify that all logs returned belong to the customer admin's organization
    for log in data["logs"]:
        if log.get("user_id"):
            result = await db.execute(select(User).filter(User.user_id == uuid.UUID(log["user_id"])))
            user = result.scalars().first()
            if user:
                assert user.customer_id == customer_admin_user.customer_id


@pytest.mark.asyncio
async def test_get_audit_logs_unauthorized(client: TestClient):
    """Test unauthorized access to audit logs"""
    response = client.get(f"{settings.API_V1_STR}/audit-logs")
    assert response.status_code == 401


# Test filtering
@pytest.mark.asyncio
async def test_filter_audit_logs_by_user_id(client: TestClient, admin_token: str, admin_user: User, db: AsyncSession):
    """Test filtering audit logs by user_id"""
    await log_action(db, user_id=admin_user.user_id, action_type="SPECIFIC_ACTION", resource_type="USER", resource_id=str(admin_user.user_id))

    response = client.get(
        f"{settings.API_V1_STR}/audit-logs?user_id={admin_user.user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    for log in data["logs"]:
        assert log["user_id"] == str(admin_user.user_id)

@pytest.mark.asyncio
async def test_filter_audit_logs_by_action_type(client: TestClient, admin_token: str, db: AsyncSession):
    """Test filtering audit logs by action_type"""
    await log_action(db, user_id=None, action_type="UNIQUE_ACTION_TYPE", resource_type="SYSTEM", resource_id="system-test")

    response = client.get(
        f"{settings.API_V1_STR}/audit-logs?action_type=UNIQUE_ACTION_TYPE",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) > 0
    for log in data["logs"]:
        assert log["action_type"] == "UNIQUE_ACTION_TYPE"


# Test statistics endpoint
@pytest.mark.asyncio
async def test_get_audit_log_statistics_admin(client: TestClient, admin_token: str):
    """Test admin getting audit log statistics"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/statistics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_logs" in data
    assert "logs_by_action_type" in data
    assert "logs_by_resource_type" in data


@pytest.mark.asyncio
async def test_get_audit_log_statistics_unauthorized(client: TestClient, customer_admin_token: str):
    """Test customer user attempting to get statistics (unauthorized)"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/statistics",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    assert response.status_code == 403

# Test recent activity
@pytest.mark.asyncio
async def test_get_recent_activity(client: TestClient, admin_token: str):
    """Test getting recent activity"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/recent-activity?hours=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test action/resource types
@pytest.mark.asyncio
async def test_get_action_types(client: TestClient, admin_token: str):
    """Test getting all available action types"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/action-types",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "LOGIN" in data
    assert "USER_CREATE" in data

@pytest.mark.asyncio
async def test_get_resource_types(client: TestClient, admin_token: str):
    """Test getting all available resource types"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/resource-types",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "USER" in data
    assert "DEVICE" in data

# Test export
@pytest.mark.asyncio
async def test_export_audit_logs_csv(client: TestClient, admin_token: str):
    """Test exporting audit logs as CSV"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/export?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]
    # Check that the content is valid CSV
    assert "Timestamp,User Email" in response.text

@pytest.mark.asyncio
async def test_export_audit_logs_json(client: TestClient, admin_token: str):
    """Test exporting audit logs as JSON"""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/export?format=json",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert ".json" in response.headers["content-disposition"]
    # Check that the content is valid JSON
    import json
    try:
        json.loads(response.text)
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in export")