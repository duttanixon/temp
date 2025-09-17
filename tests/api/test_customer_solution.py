"""
Test cases for customer solution management routes.
"""
import pytest
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AuditLog, Customer, CustomerSolution, LicenseStatus, User, Solution
from app.core.config import settings


# Test cases for getting customer solutions (GET /customer-solutions)
@pytest.mark.asyncio
async def test_get_customer_solutions_admin(client: TestClient, admin_token: str, db: AsyncSession):
    """Test admin getting all customer solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # We created at least one customer solution in our seed data
    
    # Check structure of returned customer solutions
    customer_solution = data[0]
    assert "id" in customer_solution
    assert "customer_id" in customer_solution
    assert "solution_id" in customer_solution
    assert "license_status" in customer_solution


@pytest.mark.asyncio
async def test_get_customer_solutions_engineer(client: TestClient, engineer_token: str):
    """Test engineer getting all customer solutions"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {engineer_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_get_customer_solutions_for_specific_customer(client: TestClient, admin_token: str, customer: Customer):
    """Test getting customer solutions for a specific customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions?customer_id={customer.customer_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned customer solutions should belong to the specified customer
    for cs in data:
        assert str(cs["customer_id"]) == str(customer.customer_id)


@pytest.mark.asyncio
async def test_get_customer_solutions_customer_admin_different_customer(client: TestClient, customer_admin_token: str, suspended_customer: Customer):
    """Test customer admin attempting to get customer solutions for a different customer"""
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions?customer_id={suspended_customer.customer_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403

# # Test cases for creating customer solutions (POST /customer-solutions)
# @pytest.mark.asyncio
# async def test_create_customer_solution_admin(client: TestClient, db: AsyncSession, admin_token: str, customer: Customer):
#     """Test admin creating a new customer solution"""
#     # Get a solution that doesn't yet have a customer solution for our customer
#     result = await db.execute(select(Solution).filter(Solution.name == "Beta Solution"))
#     solution = result.scalars().first()
    
#     customer_solution_data = {
#         "customer_id": str(customer.customer_id),
#         "solution_id": str(solution.solution_id),
#         "license_status": "ACTIVE",
#         "max_devices": 5,
#         "expiration_date": (date.today() + timedelta(days=365)).isoformat(),  # One year from now
#         "configuration_template": {"param1": "custom1", "param2": "custom2"}
#     }
    
#     response = client.post(
#         f"{settings.API_V1_STR}/customer-solutions",
#         headers={"Authorization": f"Bearer {admin_token}"},
#         json=customer_solution_data
#     )
    
#     # Check response
#     assert response.status_code == 200
#     data = response.json()
#     assert str(data["customer_id"]) == customer_solution_data["customer_id"]
#     assert str(data["solution_id"]) == customer_solution_data["solution_id"]
#     assert data["max_devices"] == customer_solution_data["max_devices"]
#     assert "id" in data
    
#     # Verify customer solution was created in database
#     await db.commit()
#     await db.refresh_all()
#     result = await db.execute(select(CustomerSolution).filter(
#         CustomerSolution.customer_id == customer.customer_id,
#         CustomerSolution.solution_id == solution.solution_id
#     ))
#     created_cs = result.scalars().first()
#     assert created_cs is not None
#     assert created_cs.max_devices == customer_solution_data["max_devices"]
    
#     # Verify audit log
#     result = await db.execute(select(AuditLog).filter(
#         AuditLog.action_type == "CUSTOMER_SOLUTION_CREATE",
#         AuditLog.resource_id == str(created_cs.id)
#     ))
#     audit_log = result.scalars().first()
#     assert audit_log is not None


@pytest.mark.asyncio
async def test_create_customer_solution_already_exists(client: TestClient, db: AsyncSession, admin_token: str, customer: Customer):
    """Test creating a customer solution that already exists"""
    # Get an existing customer solution
    result = await db.execute(select(CustomerSolution).filter(
        CustomerSolution.customer_id == customer.customer_id
    ))
    existing_cs = result.scalars().first()
    
    customer_solution_data = {
        "customer_id": str(existing_cs.customer_id),
        "solution_id": str(existing_cs.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 10
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Customer already has access to solution Test Solution" in data["detail"]


@pytest.mark.asyncio
async def test_create_customer_solution_nonexistent_customer(client: TestClient, admin_token: str, db: AsyncSession):
    """Test creating a customer solution with non-existent customer"""
    # Get a valid solution id
    result = await db.execute(select(Solution))
    solution = result.scalars().first()
    nonexistent_id = uuid.uuid4()
    
    customer_solution_data = {
        "customer_id": str(nonexistent_id),
        "solution_id": str(solution.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer not found" in data["detail"]


@pytest.mark.asyncio
async def test_create_customer_solution_nonexistent_solution(client: TestClient, admin_token: str, customer: Customer):
    """Test creating a customer solution with non-existent solution"""
    nonexistent_id = uuid.uuid4()
    
    customer_solution_data = {
        "customer_id": str(customer.customer_id),
        "solution_id": str(nonexistent_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should fail
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Solution not found" in data["detail"]


@pytest.mark.asyncio
async def test_create_customer_solution_non_admin(client: TestClient, customer_admin_token: str, db: AsyncSession, customer: Customer):
    """Test non-admin attempting to create a customer solution"""
    # Get a solution
    result = await db.execute(select(Solution))
    solution = result.scalars().first()
    
    customer_solution_data = {
        "customer_id": str(customer.customer_id),
        "solution_id": str(solution.solution_id),
        "license_status": "ACTIVE",
        "max_devices": 5
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=customer_solution_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

@pytest.mark.asyncio
async def test_get_customer_solution_nonexistent_id(client: TestClient, admin_token: str):
    """Test getting customer solution with non-existent ID"""
    nonexistent_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/customer-solutions/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Not Found" in data["detail"]

# Test cases for updating customer solution (PUT /customer-solutions/{id})
@pytest.mark.asyncio
async def test_update_customer_solution_admin(client: TestClient, db: AsyncSession, admin_token: str):
    """Test admin updating a customer solution"""
    # Get a customer solution ID from database
    result = await db.execute(select(CustomerSolution))
    cs = result.scalars().first()
    
    update_data = {
        "max_devices": 20,
        "license_status": "SUSPENDED",
        "expiration_date": (date.today() + timedelta(days=180)).isoformat()  # 6 months from now
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["license_status"] == update_data["license_status"]
    
    # Verify database updates
    await db.commit()
    await db.refresh(cs)
    result = await db.execute(select(CustomerSolution).filter(CustomerSolution.id == cs.id))
    updated_cs = result.scalars().first()
    assert updated_cs.license_status == LicenseStatus.SUSPENDED
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_UPDATE",
        AuditLog.resource_id == str(cs.id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None

@pytest.mark.asyncio
async def test_update_customer_solution_non_admin(client: TestClient, customer_admin_token: str, db: AsyncSession):
    """Test non-admin attempting to update a customer solution"""
    # Get a customer solution ID from database
    result = await db.execute(select(CustomerSolution))
    cs = result.scalars().first()
    
    update_data = {
        "max_devices": 30
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]


@pytest.mark.asyncio
async def test_update_customer_solution_nonexistent_id(client: TestClient, admin_token: str):
    """Test updating a non-existent customer solution"""
    nonexistent_id = uuid.uuid4()
    
    update_data = {
        "max_devices": 15
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/customer-solutions/customer/{nonexistent_id}/solution/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Customer solution not found" in data["detail"]

# Test cases for suspending customer solution (POST /customer-solutions/{id}/suspend)
@pytest.mark.asyncio
async def test_suspend_customer_solution(client: TestClient, db: AsyncSession, admin_token: str):
    """Test suspending a customer solution"""
    # Get an active customer solution
    result = await db.execute(select(CustomerSolution).filter(
        CustomerSolution.license_status == LicenseStatus.ACTIVE
    ))
    cs = result.scalars().first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["license_status"] == "SUSPENDED"
    
    # Verify database update
    await db.commit()
    await db.refresh(cs)
    result = await db.execute(select(CustomerSolution).filter(CustomerSolution.id == cs.id))
    suspended_cs = result.scalars().first()
    assert suspended_cs.license_status == LicenseStatus.SUSPENDED
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_SUSPEND",
        AuditLog.resource_id == str(cs.id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None


@pytest.mark.asyncio
async def test_suspend_customer_solution_non_admin(client: TestClient, customer_admin_token: str, db: AsyncSession):
    """Test non-admin attempting to suspend a customer solution"""
    # Get a customer solution ID from database
    result = await db.execute(select(CustomerSolution))
    cs = result.scalars().first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]

# Test cases for activating customer solution (POST /customer-solutions/{id}/activate)
@pytest.mark.asyncio
async def test_activate_customer_solution(client: TestClient, db: AsyncSession, admin_token: str):
    """Test activating a suspended customer solution"""
    # First suspend a customer solution
    result = await db.execute(select(CustomerSolution).filter(
        CustomerSolution.license_status == LicenseStatus.ACTIVE
    ))
    cs = result.scalars().first()
    
    # Use the API to suspend it
    suspend_response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert suspend_response.status_code == 200
    
    # Now try to activate it
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["license_status"] == "ACTIVE"
    
    # Verify database update
    await db.commit()
    result = await db.execute(select(CustomerSolution).filter(CustomerSolution.id == cs.id))
    activated_cs = result.scalars().first()
    assert activated_cs.license_status == LicenseStatus.ACTIVE
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "CUSTOMER_SOLUTION_ACTIVATE",
        AuditLog.resource_id == str(cs.id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None


@pytest.mark.asyncio
async def test_activate_customer_solution_non_admin(client: TestClient, customer_admin_token: str, db: AsyncSession):
    """Test non-admin attempting to activate a customer solution"""
    # Get a customer solution ID from database
    result = await db.execute(select(CustomerSolution))
    cs = result.scalars().first()
    
    response = client.post(
        f"{settings.API_V1_STR}/customer-solutions/customer/{cs.customer_id}/solution/{cs.solution_id}/activate",
        headers={"Authorization": f"Bearer {customer_admin_token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "enough privileges" in data["detail"]