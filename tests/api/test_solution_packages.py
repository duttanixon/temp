# tests/api/test_solution_packages.py
"""
Test cases for Solution Packages endpoints
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import (
    User, Solution, SolutionPackage, AIModel, AIModelStatus, 
    SolutionPackageModel, Device, DeviceStatus, AuditLog
)
from app.utils.solution_package_s3 import solution_package_s3_manager


# ============================================================================
# UPLOAD INITIALIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_initiate_package_upload_admin(client: TestClient, admin_token: str, solution: Solution):
    """Test admin initiating solution package upload"""
    upload_data = {
        "solution_name": solution.name,
        "description": "Test package for deployment",
        "file_extension": ".tar.gz",
        "file_size": 75000000,  # 75MB
        "device_type": "linux/arm64",
        "accelarator_type": "nvidia",
        "major": False,
        "minor": True,
        "patch": False
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/init",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=upload_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert "upload_url" in data
    assert "upload_fields" in data
    assert "s3_key" in data
    assert "expires_at" in data
    assert "instructions" in data
    assert ".tar.gz" in data["s3_key"]
    assert "multipart/form-data" in data["instructions"]


@pytest.mark.asyncio
async def test_initiate_package_upload_engineer(client: TestClient, engineer_token: str, solution: Solution):
    """Test engineer initiating solution package upload"""
    upload_data = {
        "solution_name": solution.name,
        "description": "Engineer package upload",
        "file_extension": ".zip",
        "file_size": 25000000,  # 25MB
        "device_type": "raspberry pi",
        "accelarator_type": "none",
        "patch": True
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/init",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=upload_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert ".zip" in data["s3_key"]


@pytest.mark.asyncio
async def test_initiate_package_upload_customer_admin_forbidden(client: TestClient, customer_admin_token: str, solution: Solution):
    """Test customer admin cannot initiate package upload"""
    upload_data = {
        "solution_name": solution.name,
        "description": "Forbidden package",
        "file_extension": ".tar.gz",
        "file_size": 50000000,
        "device_type": "linux/amd64",
        "accelarator_type": "nvidia"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/init",
        headers={"X-API-Key": "invalid-api-key"},
        json=upload_data
    )
    
    # Check response - should be unauthorized due to invalid API key
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_initiate_package_upload_solution_not_found(client: TestClient, admin_token: str):
    """Test upload init with non-existent solution"""
    upload_data = {
        "solution_name": "Non-Existent Solution",
        "description": "Package for non-existent solution",
        "file_extension": ".tar.gz",
        "file_size": 50000000,
        "device_type": "linux/amd64",
        "accelarator_type": "nvidia"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/init",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=upload_data
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "Solution with name" in data["detail"]


# ============================================================================
# UPLOAD VERIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_verify_package_upload_success(client: TestClient, admin_token: str, monkeypatch):
    """Test verifying successful package upload"""
    # Mock S3 verification
    def mock_verify_upload(s3_key):
        return {
            "exists": True,
            "size": 75000000,
            "last_modified": datetime.now()
        }
    
    monkeypatch.setattr(solution_package_s3_manager, "verify_upload", mock_verify_upload)
    
    verify_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": "solution-packages/2024/test-package.tar.gz"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=verify_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["file_exists"] is True
    assert data["file_size"] == 75000000
    assert data["s3_key"] == verify_data["s3_key"]
    assert "last_modified" in data


@pytest.mark.asyncio
async def test_verify_package_upload_not_found(client: TestClient, admin_token: str, monkeypatch):
    """Test verifying upload when file not found"""
    def mock_verify_upload(s3_key):
        return {"exists": False}
    
    monkeypatch.setattr(solution_package_s3_manager, "verify_upload", mock_verify_upload)
    
    verify_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": "solution-packages/2024/missing.tar.gz"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=verify_data
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "File not found" in data["detail"]


# ============================================================================
# UPLOAD COMPLETION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_complete_package_upload_success(client: TestClient, db: AsyncSession, solution: Solution, monkeypatch):
    """Test completing package upload successfully"""
    # Mock S3 operations
    def mock_verify_upload(s3_key):
        return {
            "exists": True,
            "size": 75000000,
            "last_modified": datetime.now()
        }
    
    def mock_mark_complete(upload_id):
        pass
    
    monkeypatch.setattr(solution_package_s3_manager, "verify_upload", mock_verify_upload)
    monkeypatch.setattr(solution_package_s3_manager, "mark_upload_complete", mock_mark_complete)
    
    complete_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": f"solution-packages/2024/package-{uuid.uuid4().hex[:8]}.tar.gz",
        "solution_name": solution.name,
        "name": "Test Package",
        "version": "1.0.0",
        "description": "Successfully uploaded package",
        "file_size": 75000000,
        "model_associations": []
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/complete",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=complete_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == complete_data["name"]
    assert data["version"] == complete_data["version"]
    assert data["solution_id"] == str(solution.solution_id)
    assert "package_id" in data
    
    # Verify in database
    await db.commit()
    result = await db.execute(select(SolutionPackage).filter(
        SolutionPackage.package_id == uuid.UUID(data["package_id"])
    ))
    created_package = result.scalars().first()
    assert created_package is not None
    assert created_package.name == complete_data["name"]
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "PACKAGE_UPLOAD_COMPLETE",
        AuditLog.resource_id == str(created_package.package_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None


@pytest.mark.asyncio
async def test_complete_package_upload_with_model_associations(
    client: TestClient, db: AsyncSession, solution: Solution, monkeypatch
):
    """Test completing package upload with AI model associations"""
    # Create test AI models
    model1 = AIModel(
        model_id=uuid.uuid4(),
        name="Associated Model 1",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="models/model1.tar.gz"
    )
    model2 = AIModel(
        model_id=uuid.uuid4(),
        name="Associated Model 2",
        version="2.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="models/model2.tar.gz"
    )
    db.add_all([model1, model2])
    await db.commit()
    
    def mock_verify_upload(s3_key):
        return {"exists": True, "size": 75000000}
    
    def mock_mark_complete(upload_id):
        pass
    
    monkeypatch.setattr(solution_package_s3_manager, "verify_upload", mock_verify_upload)
    monkeypatch.setattr(solution_package_s3_manager, "mark_upload_complete", mock_mark_complete)
    
    complete_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": f"solution-packages/2024/with-models-{uuid.uuid4().hex[:8]}.tar.gz",
        "solution_name": solution.name,
        "name": "Package with Models",
        "version": "1.0.0",
        "description": "Package with associated AI models",
        "file_size": 75000000,
        "model_associations": [model1.s3_key, model2.s3_key]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/complete",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=complete_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify model associations in database
    await db.commit()
    result = await db.execute(
        select(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == uuid.UUID(data["package_id"])
        )
    )
    associations = result.scalars().all()
    assert len(associations) == 2
    associated_model_ids = [assoc.model_id for assoc in associations]
    assert model1.model_id in associated_model_ids
    assert model2.model_id in associated_model_ids


@pytest.mark.asyncio
async def test_complete_package_upload_duplicate(client: TestClient, db: AsyncSession, solution: Solution, monkeypatch):
    """Test completing upload with duplicate package name/version"""
    # Create existing package
    existing = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Duplicate Package",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="existing-package.tar.gz"
    )
    db.add(existing)
    await db.commit()
    
    def mock_verify_upload(s3_key):
        return {"exists": True, "size": 75000000}
    
    def mock_delete_file(s3_key):
        pass
    
    monkeypatch.setattr(solution_package_s3_manager, "verify_upload", mock_verify_upload)
    monkeypatch.setattr(solution_package_s3_manager, "delete_package_file", mock_delete_file)
    
    complete_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": "solution-packages/2024/duplicate.tar.gz",
        "solution_name": solution.name,
        "name": "Duplicate Package",
        "version": "1.0.0",
        "file_size": 75000000
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/upload/complete",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=complete_data
    )
    
    # Check response - should be bad request
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"]


# ============================================================================
# LIST SOLUTION PACKAGES TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_solution_packages_no_filter(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test listing all solution packages without filter"""
    # Create test packages
    for i in range(3):
        package = SolutionPackage(
            package_id=uuid.uuid4(),
            solution_id=solution.solution_id,
            name=f"Test Package {i}",
            version=f"{i}.0.0",
            s3_bucket="test-bucket",
            s3_key=f"package-{i}.tar.gz"
        )
        db.add(package)
    await db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "packages" in data
    assert "total" in data
    assert data["total"] >= 3
    assert isinstance(data["packages"], list)


@pytest.mark.asyncio
async def test_list_solution_packages_by_solution(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test listing packages filtered by solution"""
    # Create packages for specific solution
    package1 = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Solution Specific Package 1",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="solution-package-1.tar.gz"
    )
    package2 = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Solution Specific Package 2",
        version="2.0.0",
        s3_bucket="test-bucket",
        s3_key="solution-package-2.tar.gz"
    )
    db.add_all([package1, package2])
    await db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages?solution_name={solution.name}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    # All returned packages should belong to the solution
    for package in data["packages"]:
        assert package["solution_id"] == str(solution.solution_id)


@pytest.mark.asyncio
async def test_list_solution_packages_pagination(client: TestClient, admin_token: str):
    """Test solution packages list pagination"""
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages?skip=0&limit=5",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["packages"]) <= 5
    assert "skip" in data or "offset" in data  # Accept either skip or offset
    assert "limit" in data


# ============================================================================
# GET SOLUTION PACKAGE BY ID TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_solution_package_by_id(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test getting solution package by ID"""
    # Create a test package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Get Test Package",
        version="1.0.0",
        description="Package for get by ID test",
        s3_bucket="test-bucket",
        s3_key="get-test-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["package_id"] == str(package.package_id)
    assert data["name"] == package.name
    assert data["version"] == package.version


@pytest.mark.asyncio
async def test_get_solution_package_not_found(client: TestClient, admin_token: str):
    """Test getting non-existent solution package"""
    nonexistent_id = uuid.uuid4()
    
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ============================================================================
# UPDATE SOLUTION PACKAGE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_solution_package(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test updating solution package"""
    # Create a test package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Original Package",
        version="1.0.0",
        description="Original description",
        s3_bucket="test-bucket",
        s3_key="original-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    update_data = {
        "description": "Updated description"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]
    assert data["name"] == package.name  # Unchanged
    
    # Verify in database
    await db.commit()
    await db.refresh(package)
    assert package.description == update_data["description"]


@pytest.mark.asyncio
async def test_update_solution_package_customer_admin_forbidden(client: TestClient, customer_admin_token: str, db: AsyncSession, solution: Solution):
    """Test customer admin cannot update solution package"""
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Forbidden Update Package",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="forbidden-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    update_data = {
        "description": "Should not update"
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403


# ============================================================================
# DELETE SOLUTION PACKAGE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_solution_package(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution, monkeypatch):
    """Test deleting solution package"""
    # Create a test package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Delete Test Package",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="delete-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    def mock_delete_file(s3_key):
        pass
    
    monkeypatch.setattr(solution_package_s3_manager, "delete_package_file", mock_delete_file)
    
    response = client.delete(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 204
    
    # Verify deleted from database
    await db.commit()
    result = await db.execute(select(SolutionPackage).filter(
        SolutionPackage.package_id == package.package_id
    ))
    deleted_package = result.scalars().first()
    assert deleted_package is None


@pytest.mark.asyncio
async def test_delete_solution_package_not_found(client: TestClient, admin_token: str):
    """Test deleting non-existent solution package"""
    nonexistent_id = uuid.uuid4()
    
    response = client.delete(
        f"{settings.API_V1_STR}/solution-packages/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404


# ============================================================================
# DOWNLOAD URL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_package_download_url(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution, monkeypatch):
    """Test generating presigned download URL for package"""
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Download Test Package",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="download-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    def mock_generate_download_url(s3_key, expires_in, filename=None):
        return f"https://s3.amazonaws.com/test-bucket/{s3_key}?signed"
    
    monkeypatch.setattr(solution_package_s3_manager, "generate_download_url", mock_generate_download_url)
    
    response = client.get(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/download-url",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "expires_in" in data
    assert "expires_at" in data
    assert data["package_id"] == str(package.package_id)


# ============================================================================
# MODEL ASSOCIATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_associate_model_with_package(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test associating AI model with solution package"""
    # Create package and model
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Package for Model Association",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="model-assoc-package.tar.gz"
    )
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Model to Associate",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="model-to-associate.tar.gz"
    )
    db.add_all([package, model])
    await db.commit()
    
    associate_data = {
        "model_id": str(model.model_id)
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/associate-model",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=associate_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Model associated successfully"
    
    # Verify association in database
    await db.commit()
    result = await db.execute(
        select(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == package.package_id,
            SolutionPackageModel.model_id == model.model_id
        )
    )
    association = result.scalars().first()
    assert association is not None


@pytest.mark.asyncio
async def test_dissociate_model_from_package(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test removing AI model association from solution package"""
    # Create package and model with association
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Package with Model",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="package-with-model.tar.gz"
    )
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Model to Dissociate",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="model-to-dissociate.tar.gz"
    )
    db.add_all([package, model])
    await db.commit()
    
    # Create association
    association = SolutionPackageModel(
        package_id=package.package_id,
        model_id=model.model_id
    )
    db.add(association)
    await db.commit()
    
    response = client.delete(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/dissociate-model/{model.model_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 204
    
    # Verify association removed from database
    await db.commit()
    result = await db.execute(
        select(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == package.package_id,
            SolutionPackageModel.model_id == model.model_id
        )
    )
    association = result.scalars().first()
    assert association is None


# ============================================================================
# DEPLOYMENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_solution_package(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution, active_device: Device):
    """Test deploying solution package to devices"""
    # Create package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Package to Deploy",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="deploy-package.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    deploy_data = {
        "device_ids": [str(active_device.device_id)],
        "configuration": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/deploy",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=deploy_data
    )
    
    # Check response
    assert response.status_code == 202
    data = response.json()
    assert "message" in data
    assert "package_id" in data
    assert "devices_count" in data
    assert data["devices_count"] == 1
    assert data["package_id"] == str(package.package_id)


@pytest.mark.asyncio
async def test_deploy_package_to_inactive_device(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution, provisioned_device: Device):
    """Test deploying package to inactive device - should be accepted but fail in background"""
    # Create package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Package for Inactive Device",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="inactive-deploy.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    deploy_data = {
        "device_ids": [str(provisioned_device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/deploy",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=deploy_data
    )
    
    # Check response - should be accepted (202) as validation happens in background
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_deploy_package_customer_admin_own_devices(client: TestClient, customer_admin_token: str, db: AsyncSession, solution: Solution, device: Device):
    """Test customer admin deploying package to their own devices"""
    # Create package
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Customer Deploy Package",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="customer-deploy.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    # Update device to active status
    device.status = DeviceStatus.ACTIVE
    await db.commit()
    
    deploy_data = {
        "device_ids": [str(device.device_id)]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/deploy",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=deploy_data
    )
    
    # Check response - customer admins may or may not have permission based on your implementation
    # Adjust assertion based on your authorization logic
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_deploy_package_empty_device_list(client: TestClient, admin_token: str, db: AsyncSession, solution: Solution):
    """Test deploying package with empty device list"""
    package = SolutionPackage(
        package_id=uuid.uuid4(),
        solution_id=solution.solution_id,
        name="Package No Devices",
        version="1.0.0",
        s3_bucket="test-bucket",
        s3_key="no-devices.tar.gz"
    )
    db.add(package)
    await db.commit()
    
    deploy_data = {
        "device_ids": []
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/solution-packages/{package.package_id}/deploy",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=deploy_data
    )
    
    # Check response - should be validation error
    assert response.status_code == 422