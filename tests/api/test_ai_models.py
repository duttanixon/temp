"""
Test cases for AI Models endpoints
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
from app.models import User, AIModel, AIModelStatus, AuditLog
from app.utils.ai_model_s3 import ai_model_s3_manager


# ============================================================================
# UPLOAD INITIALIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_initiate_upload_admin(client: TestClient, admin_token: str):
    """Test admin initiating AI model upload"""
    upload_data = {
        "name": "Test Model",
        "version": "1.0.0",
        "status": "ACTIVE",
        "file_extension": ".tar.gz",
        "file_size": 50000000,  # 50MB
        "device_type": "GPU",
        "accelerator_type": "NVIDIA"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/init",
        headers={"Authorization": f"Bearer {admin_token}"},
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


@pytest.mark.asyncio
async def test_initiate_upload_engineer(client: TestClient, engineer_token: str):
    """Test engineer initiating AI model upload"""
    upload_data = {
        "name": "Engineer Model",
        "version": "2.0.0",
        "status": "IN_TESTING",
        "file_extension": ".h5",
        "file_size": 100000000,  # 100MB
        "device_type": "CPU",
        "accelerator_type": "AMD"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/init",
        headers={"Authorization": f"Bearer {engineer_token}"},
        json=upload_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert ".h5" in data["s3_key"]


@pytest.mark.asyncio
async def test_initiate_upload_customer_admin_forbidden(client: TestClient, customer_admin_token: str):
    """Test customer admin cannot initiate AI model upload"""
    upload_data = {
        "name": "Forbidden Model",
        "version": "1.0.0",
        "status": "ACTIVE",
        "file_extension": ".tar.gz",
        "file_size": 50000000,
        "device_type": "GPU",
        "accelerator_type": "NVIDIA"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/init",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=upload_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_initiate_upload_invalid_file_size(client: TestClient, admin_token: str):
    """Test upload with invalid file size (too large)"""
    upload_data = {
        "name": "Large Model",
        "version": "1.0.0",
        "status": "ACTIVE",
        "file_extension": ".tar.gz",
        "file_size": 2000000000,  # 2GB - over limit
        "device_type": "GPU",
        "accelerator_type": "NVIDIA"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/init",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=upload_data
    )
    
    # Check response - should be validation error
    assert response.status_code == 422


# ============================================================================
# BATCH UPLOAD VERIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_verify_batch_upload_success(client: TestClient, admin_token: str, monkeypatch):
    """Test verifying successful batch upload"""
    # Mock S3 verification
    def mock_verify_upload(s3_key):
        return {
            "exists": True,
            "size": 50000000,
            "last_modified": datetime.now()
        }
    
    monkeypatch.setattr(ai_model_s3_manager, "verify_upload", mock_verify_upload)
    
    verify_data = {
        "s3_keys": [
            "ai-models/2024/model1.tar.gz",
            "ai-models/2024/model2.tar.gz",
            "ai-models/2024/model3.tar.gz"
        ]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/verify",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=verify_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "SUCCESS"
    assert "details" in data
    assert len(data["details"]) == 3
    for detail in data["details"]:
        assert detail["exists"] is True
        assert detail["size"] == 50000000


@pytest.mark.asyncio
async def test_verify_batch_upload_partial_failure(client: TestClient, admin_token: str, monkeypatch):
    """Test verifying batch upload with some missing files"""
    def mock_verify_upload(s3_key):
        if "model2" in s3_key:
            return {"exists": False}
        return {
            "exists": True,
            "size": 50000000,
            "last_modified": datetime.now()
        }
    
    monkeypatch.setattr(ai_model_s3_manager, "verify_upload", mock_verify_upload)
    
    verify_data = {
        "s3_keys": [
            "ai-models/2024/model1.tar.gz",
            "ai-models/2024/model2.tar.gz",
            "ai-models/2024/model3.tar.gz"
        ]
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/verify",
        headers={"X-API-Key": settings.INTERNAL_API_KEY},
        json=verify_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "FAILED"
    assert data["details"][1]["exists"] is False


# ============================================================================
# UPLOAD COMPLETION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_complete_upload_success(client: TestClient, db: AsyncSession, admin_token: str, monkeypatch):
    """Test completing AI model upload successfully"""
    # Mock S3 verification
    def mock_verify_upload(s3_key):
        return {
            "exists": True,
            "size": 50000000,
            "last_modified": datetime.now()
        }
    
    def mock_mark_complete(upload_id):
        pass
    
    monkeypatch.setattr(ai_model_s3_manager, "verify_upload", mock_verify_upload)
    monkeypatch.setattr(ai_model_s3_manager, "mark_upload_complete", mock_mark_complete)
    
    complete_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": f"ai-models/2024/test-model-{uuid.uuid4().hex[:8]}.tar.gz",
        "name": "Completed Model",
        "version": "1.0.0",
        "description": "A successfully uploaded model",
        "status": "ACTIVE",
        "file_size": 50000000
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/complete",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=complete_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == complete_data["name"]
    assert data["version"] == complete_data["version"]
    assert data["s3_key"] == complete_data["s3_key"]
    assert "model_id" in data
    
    # Verify in database
    await db.commit()
    result = await db.execute(select(AIModel).filter(AIModel.name == complete_data["name"]))
    created_model = result.scalars().first()
    assert created_model is not None
    assert created_model.name == complete_data["name"]
    
    # Verify audit log
    result = await db.execute(select(AuditLog).filter(
        AuditLog.action_type == "AI_MODEL_CREATE",
        AuditLog.resource_id == str(created_model.model_id)
    ))
    audit_log = result.scalars().first()
    assert audit_log is not None


@pytest.mark.asyncio
async def test_complete_upload_file_not_found(client: TestClient, admin_token: str, monkeypatch):
    """Test completing upload when file not found in S3"""
    def mock_verify_upload(s3_key):
        return {"exists": False}
    
    monkeypatch.setattr(ai_model_s3_manager, "verify_upload", mock_verify_upload)
    
    complete_data = {
        "upload_id": str(uuid.uuid4()),
        "s3_key": "ai-models/2024/nonexistent.tar.gz",
        "name": "Missing Model",
        "version": "1.0.0",
        "status": "ACTIVE",
        "file_size": 50000000
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/ai-models/upload/complete",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=complete_data
    )
    
    # Check response - should be bad request
    assert response.status_code == 400
    data = response.json()
    assert "File not found" in data["detail"]


# ============================================================================
# LIST AI MODELS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_ai_models_no_filter(client: TestClient, admin_token: str, db: AsyncSession):
    """Test listing all AI models without filter"""
    # Create some test models
    for i in range(3):
        model = AIModel(
            model_id=uuid.uuid4(),
            name=f"Test Model {i}",
            version=f"{i}.0.0",
            status=AIModelStatus.ACTIVE,
            s3_bucket="test-bucket",
            s3_key=f"test-key-{i}"
        )
        db.add(model)
    await db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "total" in data
    assert data["total"] >= 3
    assert isinstance(data["models"], list)


@pytest.mark.asyncio
async def test_list_ai_models_with_status_filter(client: TestClient, admin_token: str, db: AsyncSession):
    """Test listing AI models filtered by status"""
    # Create models with different statuses
    active_model = AIModel(
        model_id=uuid.uuid4(),
        name="Active Model",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="active-model"
    )
    deprecated_model = AIModel(
        model_id=uuid.uuid4(),
        name="Deprecated Model",
        version="1.0.0",
        status=AIModelStatus.DEPRECATED,
        s3_bucket="test-bucket",
        s3_key="deprecated-model"
    )
    db.add(active_model)
    db.add(deprecated_model)
    await db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models?status=ACTIVE",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    # All returned models should be ACTIVE
    for model in data["models"]:
        assert model["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_ai_models_pagination(client: TestClient, admin_token: str):
    """Test AI models list pagination"""
    response = client.get(
        f"{settings.API_V1_STR}/ai-models?skip=0&limit=5",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) <= 5
    assert data["skip"] == 0
    assert data["limit"] == 5


@pytest.mark.asyncio
async def test_list_ai_models_sort_by_created(client: TestClient, admin_token: str):
    """Test listing AI models sorted by creation date"""
    response = client.get(
        f"{settings.API_V1_STR}/ai-models?sort_by=created_at&sort_order=desc",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    models = data["models"]
    
    # Verify descending order
    if len(models) > 1:
        for i in range(len(models) - 1):
            assert models[i]["created_at"] >= models[i + 1]["created_at"]


# ============================================================================
# GET AI MODEL BY ID TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_ai_model_by_id(client: TestClient, admin_token: str, db: AsyncSession):
    """Test getting AI model by ID"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Get Test Model",
        version="1.0.0",
        description="Model for get by ID test",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-get"
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == str(model.model_id)
    assert data["name"] == model.name
    assert data["version"] == model.version


@pytest.mark.asyncio
async def test_get_ai_model_not_found(client: TestClient, admin_token: str):
    """Test getting non-existent AI model"""
    nonexistent_id = uuid.uuid4()
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# ============================================================================
# DOWNLOAD URL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_download_url(client: TestClient, admin_token: str, db: AsyncSession, monkeypatch):
    """Test generating presigned download URL for AI model"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Download Test Model",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-download"
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    # Mock S3 URL generation
    def mock_generate_download_url(s3_key, expires_in=3600, filename=None):
        return f"https://s3.amazonaws.com/test-bucket/{s3_key}?signed"
    
    monkeypatch.setattr(ai_model_s3_manager, "generate_download_url", mock_generate_download_url)
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}/download-url",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "expires_in" in data
    assert "expires_at" in data
    assert data["model_id"] == str(model.model_id)
    assert "signed" in data["download_url"]


@pytest.mark.asyncio
async def test_generate_download_url_custom_expiry(client: TestClient, admin_token: str, db: AsyncSession, monkeypatch):
    """Test generating download URL with custom expiry time"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Download Custom Expiry Model",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-custom"
    )
    db.add(model)
    await db.commit()
    
    def mock_generate_download_url(s3_key, expires_in=3600, filename=None):
        return f"https://s3.amazonaws.com/test-bucket/{s3_key}?expires={expires_in}"
    
    monkeypatch.setattr(ai_model_s3_manager, "generate_download_url", mock_generate_download_url)
    
    response = client.get(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}/download-url?expires_in=7200",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["expires_in"] == 7200


# ============================================================================
# UPDATE AI MODEL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_ai_model_metadata(client: TestClient, admin_token: str, db: AsyncSession):
    """Test updating AI model metadata"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Original Name",
        version="1.0.0",
        description="Original description",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-update"
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "status": "IN_TESTING"
    }
    
    response = client.patch(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["status"] == update_data["status"]
    
    # Verify in database
    await db.commit()
    await db.refresh(model)
    assert model.name == update_data["name"]
    assert model.description == update_data["description"]
    assert model.status == AIModelStatus.IN_TESTING


@pytest.mark.asyncio
async def test_update_ai_model_partial(client: TestClient, admin_token: str, db: AsyncSession):
    """Test partial update of AI model"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Partial Update Model",
        version="2.0.0",
        description="Original description",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-partial"
    )
    db.add(model)
    await db.commit()
    
    # Update only status
    update_data = {
        "status": "DEPRECATED"
    }
    
    response = client.patch(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DEPRECATED"
    assert data["name"] == model.name  # Unchanged
    assert data["version"] == model.version  # Unchanged


@pytest.mark.asyncio
async def test_update_ai_model_customer_admin_forbidden(client: TestClient, customer_admin_token: str, db: AsyncSession):
    """Test customer admin cannot update AI model"""
    # Create a test model
    model = AIModel(
        model_id=uuid.uuid4(),
        name="Forbidden Update Model",
        version="1.0.0",
        status=AIModelStatus.ACTIVE,
        s3_bucket="test-bucket",
        s3_key="test-key-forbidden"
    )
    db.add(model)
    await db.commit()
    
    update_data = {
        "name": "Should Not Update"
    }
    
    response = client.patch(
        f"{settings.API_V1_STR}/ai-models/{model.model_id}",
        headers={"Authorization": f"Bearer {customer_admin_token}"},
        json=update_data
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_ai_model(client: TestClient, admin_token: str):
    """Test updating non-existent AI model"""
    nonexistent_id = uuid.uuid4()
    
    update_data = {
        "name": "Should Not Exist"
    }
    
    response = client.patch(
        f"{settings.API_V1_STR}/ai-models/{nonexistent_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Check response - should be not found
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()