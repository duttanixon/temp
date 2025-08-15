# app/api/routes/ai_models.py
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.api import deps
from app.crud import ai_model
from app.models import User, UserRole
from app.schemas.ai_model import (
    AIModel as AIModelSchema,
    AIModelCreate,
    AIModelUpdate,
    AIModelListResponse,
    AIModelBasic,
    UploadInitRequest,
    UploadInitResponse,
    UploadCompleteRequest,
    UploadVerifyRequest,
    UploadVerifyResponse,
    UploadCancelRequest,
    ModelDownloadUrlResponse
)
from app.models.ai_model import AIModelStatus
from app.utils.ai_model_s3 import ai_model_s3_manager
from app.utils.audit import log_action
from app.utils.logger import get_logger
from app.schemas.audit import AuditLogActionType, AuditLogResourceType

logger = get_logger("api.ai_models")

router = APIRouter()


# ============================================================================
# DIRECT UPLOAD ENDPOINTS
# ============================================================================

@router.post("/upload/init", response_model=UploadInitResponse)
async def initiate_upload(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
    upload_request: UploadInitRequest,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Step 1: Initialize direct upload to S3.
    
    This endpoint:
    1. Validates the request
    2. Checks for duplicate models
    3. Generates a presigned S3 upload URL
    4. Returns the URL for direct client upload
    
    **Permissions**: Admin and Engineer only
    
    **Returns**: Upload URL and instructions for direct S3 upload
    """
    # Validate file size
    if upload_request.file_size > 1 * 1024 * 1024 * 1024:  # 5GB
        raise HTTPException(
            status_code=413,
            detail="File size exceeds maximum allowed size of 1GB"
        )
    
    # Check if model with same name and version already exists
    existing_model = ai_model.get_by_name_and_version(
        db, name=upload_request.name, version=upload_request.version
    )
    if existing_model:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{upload_request.name}' version '{upload_request.version}' already exists"
        )
    
    # Generate presigned upload URL
    try:
        upload_info = ai_model_s3_manager.generate_presigned_upload(
            model_name=upload_request.name,
            version=upload_request.version,
            device_type=upload_request.device_type,
            accelerator_type=upload_request.accelerator_type,
            file_extension=upload_request.file_extension,
            file_size=upload_request.file_size,
            uploaded_by=current_user.email
        )
        
        # Log the initiation
        log_action(
            db=db,
            user_id=current_user.user_id,
            action_type=AuditLogActionType.AI_MODEL_CREATE,
            resource_type=AuditLogResourceType.AI_MODEL,
            resource_id=upload_info["upload_id"],
            details={
                "action": "upload_initiated",
                "model_name": upload_request.name,
                "version": upload_request.version,
                "file_size": upload_request.file_size
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"User {current_user.email} initiated upload for model "
            f"{upload_request.name} v{upload_request.version}"
        )
        
        # Schedule cleanup of expired uploads
        background_tasks.add_task(ai_model_s3_manager.cleanup_expired_uploads)
        
        return UploadInitResponse(
            upload_id=upload_info["upload_id"],
            upload_url=upload_info["upload_url"],
            upload_fields=upload_info["upload_fields"],
            s3_key=upload_info["s3_key"],
            expires_at=upload_info["expires_at"],
            instructions=(
                "Use the provided URL and fields to upload your file directly to S3. "
                "Send a POST request with multipart/form-data, including all fields "
                "from 'upload_fields' and your file as the last field named 'file'. "
                "After successful upload (204 response), call /upload/complete endpoint."
            )
        )
        
    except Exception as e:
        logger.error(f"Error initiating upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.post("/upload/verify", response_model=UploadVerifyResponse)
async def verify_upload(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    verify_request: UploadVerifyRequest
) -> Any:
    """
    Step 2 (Optional): Verify that the file was uploaded to S3.
    
    This endpoint checks if the file exists in S3 and returns its metadata.
    Useful for debugging or confirming upload before completing.
    
    **Returns**: Upload verification status and file metadata
    f4125587-97ca-40b1-b3a5-8527d6863e88
    """
    # Verify the upload exists in S3
    verification = ai_model_s3_manager.verify_upload(verify_request.s3_key)
    
    if not verification.get("exists", False):
        raise HTTPException(
            status_code=404,
            detail="File not found in S3. Upload may have failed or is still in progress."
        )
    
    logger.info(f"Verified upload for S3 key: {verify_request.s3_key}")
    
    return UploadVerifyResponse(
        upload_id=verify_request.upload_id,
        s3_key=verify_request.s3_key,
        file_exists=True,
        file_size=verification["size"],
        last_modified=verification.get("last_modified")
    )


@router.post("/upload/complete", response_model=AIModelSchema)
async def complete_upload(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
    complete_request: UploadCompleteRequest
) -> Any:
    """
    Step 3: Complete the upload process and create the model record.
    
    This endpoint:
    1. Verifies the file was uploaded to S3
    2. Creates the database record
    3. Marks the upload as complete
    4. Returns the created model
    
    **Permissions**: Admin and Engineer only
    
    **Returns**: Created AI model record
    """
    # Verify upload exists in S3
    verification = ai_model_s3_manager.verify_upload(complete_request.s3_key)
    
    if not verification.get("exists", False):
        raise HTTPException(
            status_code=400,
            detail="File not found in S3. Please ensure the file was uploaded successfully."
        )
    
    # Verify file size matches (with some tolerance)
    actual_size = verification.get("size", 0)
    print(f"Actual file size: {actual_size} bytes")
    print(f"Expected file size: {complete_request.file_size} bytes")
    if abs(actual_size - complete_request.file_size) > 1024 * 1024:  # 1MB tolerance
        logger.warning(
            f"File size mismatch for upload {complete_request.upload_id}: "
            f"expected {complete_request.file_size}, got {actual_size}"
        )
    
    # Check again for duplicate (in case of race condition)
    existing_model = ai_model.get_by_name_and_version(
        db, name=complete_request.name, version=complete_request.version
    )
    if existing_model:
        # Clean up the uploaded file since we can't use it
        ai_model_s3_manager.delete_model_file(complete_request.s3_key)
        raise HTTPException(
            status_code=400,
            detail=f"Model '{complete_request.name}' version '{complete_request.version}' already exists"
        )
    
    try:
        # Create database record
        model_in = AIModelCreate(
            name=complete_request.name,
            version=complete_request.version,
            description=complete_request.description,
            status=complete_request.status or AIModelStatus.ACTIVE
        )
        
        db_model = ai_model.create_with_s3_info(
            db,
            obj_in=model_in,
            s3_bucket=ai_model_s3_manager.bucket_name,
            s3_key=complete_request.s3_key
        )
        
        # Mark upload as complete
        ai_model_s3_manager.mark_upload_complete(complete_request.upload_id)
        
        # Log the action
        log_action(
            db=db,
            user_id=current_user.user_id,
            action_type=AuditLogActionType.AI_MODEL_CREATE,
            resource_type=AuditLogResourceType.AI_MODEL,
            resource_id=str(db_model.model_id),
            details={
                "action": "upload_completed",
                "name": complete_request.name,
                "version": complete_request.version,
                "file_size": actual_size,
                "upload_id": complete_request.upload_id,
                "s3_key": complete_request.s3_key
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"Model upload completed: {db_model.model_id} - "
            f"{complete_request.name} v{complete_request.version}"
        )
        
        return db_model
        
    except Exception as e:
        logger.error(f"Error completing upload: {str(e)}")
        # Don't delete the S3 file immediately - might be a transient DB issue
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create model record: {str(e)}"
        )


# ============================================================================
# STANDARD CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=AIModelListResponse)
def list_ai_models(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[AIModelStatus] = Query(None, description="Filter by status"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> Any:
    """
    List AI models with optional filtering and sorting.
    
    **Permissions**: All authenticated users
    
    **Returns**: Paginated list of AI models
    """
    models = ai_model.get_multi_with_filters(
        db,
        skip=skip,
        limit=limit,
        status=status,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get total count
    total = ai_model.count_with_filters(db, status=status, name=name)
    
    return AIModelListResponse(
        models=models,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{model_id}", response_model=AIModelSchema)
def get_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get AI model by ID.
    
    **Permissions**: All authenticated users
    
    **Returns**: AI model details
    """
    db_model = ai_model.get_by_id(db, model_id=model_id)
    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )
    return db_model


@router.get("/{model_id}/download-url", response_model=ModelDownloadUrlResponse)
def get_model_download_url(
    *,
    db: Session = Depends(deps.get_db),
    model_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration time in seconds")
) -> Any:
    """
    Generate a presigned download URL for the AI model.
    
    **Permissions**: All authenticated users
    
    **Returns**: Time-limited download URL
    """
    db_model = ai_model.get_by_id(db, model_id=model_id)
    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )
    
    # Generate download URL with custom filename
    filename = f"{db_model.name}_v{db_model.version}".replace(" ", "_")
    # Infer extension from S3 key
    if "." in db_model.s3_key:
        extension = "." + ".".join(db_model.s3_key.split(".")[1:])
        filename += extension
    
    download_url = ai_model_s3_manager.generate_download_url(
        s3_key=db_model.s3_key,
        expires_in=expires_in,
        filename=filename
    )
    
    expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(seconds=expires_in)
    
    return ModelDownloadUrlResponse(
        model_id=model_id,
        download_url=download_url,
        expires_in=expires_in,
        expires_at=expires_at
    )


@router.patch("/{model_id}", response_model=AIModelSchema)
def update_ai_model(
    *,
    db: Session = Depends(deps.get_db),
    model_id: uuid.UUID,
    model_in: AIModelUpdate,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> Any:
    """
    Update AI model metadata.
    
    **Permissions**: Admin and Engineer only
    
    **Returns**: Updated AI model
    """
    db_model = ai_model.get_by_id(db, model_id=model_id)
    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )
    
    # Check if updating name/version would create a duplicate
    if model_in.name or model_in.version:
        check_name = model_in.name if model_in.name else db_model.name
        check_version = model_in.version if model_in.version else db_model.version
        
        existing = ai_model.get_by_name_and_version(
            db, name=check_name, version=check_version
        )
        if existing and existing.model_id != model_id:
            raise HTTPException(
                status_code=400,
                detail=f"Model with name '{check_name}' and version '{check_version}' already exists"
            )
    
    updated_model = ai_model.update(db, db_obj=db_model, obj_in=model_in)
    
    # Log the action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.AI_MODEL_UPDATE,
        resource_type=AuditLogResourceType.AI_MODEL,
        resource_id=str(model_id),
        details=model_in.dict(exclude_unset=True),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_model