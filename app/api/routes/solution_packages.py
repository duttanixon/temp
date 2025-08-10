# app/api/routes/solution_packages.py
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks, status
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from app.api import deps
from app.crud import solution_package, solution, ai_model
from app.models import User
from app.schemas.solution_package import (
    SolutionPackage as SolutionPackageSchema,
    SolutionPackageCreate,
    SolutionPackageUpdate,
    SolutionPackageListResponse,
    PackageUploadInitRequest,
    PackageUploadInitResponse,
    PackageUploadCompleteRequest,
    PackageUploadVerifyRequest,
    PackageUploadVerifyResponse,
    PackageDownloadUrlResponse,
    PackageModelAssociationCreate
)
from app.utils.solution_package_s3 import solution_package_s3_manager
from app.utils.audit import log_action
from app.utils.logger import get_logger
from app.schemas.audit import AuditLogActionType, AuditLogResourceType

logger = get_logger("api.solution_packages")

router = APIRouter()


# ============================================================================
# DIRECT UPLOAD ENDPOINTS
# ============================================================================

@router.post("/upload/init", response_model=PackageUploadInitResponse)
async def initiate_package_upload(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    upload_request: PackageUploadInitRequest,
    background_tasks: BackgroundTasks,
    api_key_valid: bool = Depends(deps.verify_api_key),
) -> Any:
    """
    Step 1: Initialize direct upload to S3 for solution package.
    
    This endpoint:
    1. Validates the request and solution existence
    2. Checks for duplicate packages
    3. Generates a presigned S3 upload URL
    4. Returns the URL for direct client upload
    
    **Permissions**: Admin and Engineer only
    **Returns**: Upload URL and instructions for direct S3 upload
    """
    # Validate file size
    if upload_request.file_size > 1 * 1024 * 1024 * 1024:  # 1GB
        raise HTTPException(
            status_code=413,
            detail="File size exceeds maximum allowed size of 5GB"
        )
    
    # Check if solution exists
    db_solution = solution.get_by_id(db, solution_id=upload_request.solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail=f"Solution with ID {upload_request.solution_id} not found"
        )
    
    # Check if package with same name and version already exists for this solution
    existing_package = solution_package.get_by_name_and_version(
        db, 
        name=upload_request.name, 
        version=upload_request.version,
        solution_id=upload_request.solution_id
    )
    if existing_package:
        raise HTTPException(
            status_code=400,
            detail=f"Package '{upload_request.name}' version '{upload_request.version}' already exists for this solution"
        )
    
    # Generate presigned upload URL
    try:
        upload_info = solution_package_s3_manager.generate_presigned_upload(
            solution_id=str(upload_request.solution_id),
            solution_name=str(db_solution.name),
            package_name=upload_request.name,
            version=upload_request.version,
            device_type=upload_request.device_type,
            accelarator_type=upload_request.accelarator_type,
            file_extension=upload_request.file_extension,
            file_size=upload_request.file_size,
            uploaded_by="system@cicd"
        )
        
        # Log the initiation
        log_action(
            db=db,
            user_id=None,
            action_type=AuditLogActionType.PACKAGE_UPLOAD_INIT,
            resource_type=AuditLogResourceType.SOLUTION_PACKAGE,
            resource_id=upload_info["upload_id"],
            details={
                "action": "upload_initiated",
                "solution_id": str(upload_request.solution_id),
                "package_name": upload_request.name,
                "version": upload_request.version,
                "file_size": upload_request.file_size
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"CI/CD system initiated package upload for "
            f"{upload_request.name} v{upload_request.version}"
        )
        
        # Schedule cleanup of expired uploads
        background_tasks.add_task(solution_package_s3_manager.cleanup_expired_uploads)
        
        return PackageUploadInitResponse(
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
        logger.error(f"Error initiating package upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.post("/upload/verify", response_model=PackageUploadVerifyResponse)
async def verify_package_upload(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    verify_request: PackageUploadVerifyRequest
) -> Any:
    """
    Step 2 (Optional): Verify that the package file was uploaded to S3.
    
    This endpoint checks if the file exists in S3 and returns its metadata.
    Useful for debugging or confirming upload before completing.
    
    **Returns**: Upload verification status and file metadata
    """
    # Verify the upload exists in S3
    verification = solution_package_s3_manager.verify_upload(verify_request.s3_key)
    
    if not verification.get("exists", False):
        raise HTTPException(
            status_code=404,
            detail="File not found in S3. Upload may have failed or is still in progress."
        )
    
    logger.info(f"Verified package upload for S3 key: {verify_request.s3_key}")
    
    return PackageUploadVerifyResponse(
        upload_id=verify_request.upload_id,
        s3_key=verify_request.s3_key,
        file_exists=True,
        file_size=verification["size"],
        last_modified=verification.get("last_modified")
    )


@router.post("/upload/complete", response_model=SolutionPackageSchema)
async def complete_package_upload(
    *,
    db: Session = Depends(deps.get_db),
    api_key_valid: bool = Depends(deps.verify_api_key),
    request: Request,
    complete_request: PackageUploadCompleteRequest
) -> Any:
    """
    Step 3: Complete the upload process and create the package record.
    
    This endpoint:
    1. Verifies the file was uploaded to S3
    2. Creates the database record
    3. Associates AI models if specified
    4. Marks the upload as complete
    5. Returns the created package
    
    **Returns**: Created solution package record
    """
    # Verify upload exists in S3
    verification = solution_package_s3_manager.verify_upload(complete_request.s3_key)
    
    if not verification.get("exists", False):
        raise HTTPException(
            status_code=400,
            detail="File not found in S3. Please ensure the file was uploaded successfully."
        )
    
    # Get solution by name
    db_solution = solution.get_by_name(db, name=complete_request.solution_name)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail=f"Solution with name '{complete_request.solution_name}' not found"
        )

    # Verify file size matches (with some tolerance)
    actual_size = verification.get("size", 0)
    if abs(actual_size - complete_request.file_size) > 1024 * 1024:  # 1MB tolerance
        logger.warning(
            f"File size mismatch for upload {complete_request.upload_id}: "
            f"expected {complete_request.file_size}, got {actual_size}"
        )
    
    # Check again for duplicate (in case of race condition)
    existing_package = solution_package.get_by_name_and_version(
        db, 
        name=complete_request.name, 
        version=complete_request.version,
        solution_id=db_solution.solution_id
    )
    if existing_package:
        # Clean up the uploaded file since we can't use it
        solution_package_s3_manager.delete_package_file(complete_request.s3_key)
        raise HTTPException(
            status_code=400,
            detail=f"Package '{complete_request.name}' version '{complete_request.version}' already exists"
        )
    
    try:
        # Create database record
        package_in = SolutionPackageCreate(
            solution_id=db_solution.solution_id,
            name=complete_request.name,
            version=complete_request.version,
            description=complete_request.description,
            s3_bucket=solution_package_s3_manager.bucket_name,
            s3_key=complete_request.s3_key
        )
        
        db_package = solution_package.create_with_s3_info(
            db,
            obj_in=package_in,
            s3_bucket=solution_package_s3_manager.bucket_name,
            s3_key=complete_request.s3_key
        )
        
        # Associate AI models if specified
        if complete_request.model_associations:
            for model_s3_key in complete_request.model_associations:
                # Verify model exists by s3_key
                db_model = ai_model.get_by_s3_key(db, s3_key=model_s3_key)
                if db_model:
                    solution_package.associate_with_model(
                        db,
                        package_id=db_package.package_id,
                        model_id=db_model.model_id,
                    )
                else:
                    logger.warning(f"Model with S3 key {model_s3_key} not found, skipping association")
        
        # Mark upload as complete
        solution_package_s3_manager.mark_upload_complete(complete_request.upload_id)
        
        # Log the action
        log_action(
            db=db,
            user_id=None,
            action_type=AuditLogActionType.PACKAGE_UPLOAD_COMPLETE,
            resource_type=AuditLogResourceType.SOLUTION_PACKAGE,
            resource_id=str(db_package.package_id),
            details={
                "action": "upload_completed",
                "solution_id": str(db_solution.solution_id),
                "solution_name": complete_request.solution_name,
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
            f"Package upload completed: {db_package.package_id} - "
            f"{complete_request.name} v{complete_request.version}"
        )
        
        # Get solution name for response
        db_solution = solution.get_by_id(db, solution_id=db_package.solution_id)
        db_package.solution_name = db_solution.name if db_solution else None
        
        return db_package
        
    except Exception as e:
        logger.error(f"Error completing package upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create package record: {str(e)}"
        )


# ============================================================================
# STANDARD CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=SolutionPackageListResponse)
def list_packages(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    solution_name: Optional[str] = Query(None, description="Filter by solution name"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    version: Optional[str] = Query(None, description="Filter by version"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> Any:
    """
    List solution packages with optional filtering and sorting.
    
    **Permissions**: All authenticated users
    """
    solution_id = None
    db_solution = None

    if solution_name:
        # Remove any surrounding quotes from solution_name
        print(f"Filtering by solution name: {solution_name}")
        cleaned_solution_name = solution_name.strip('"\'')
        db_solution = solution.get_by_name(db, name=cleaned_solution_name)
        if not db_solution:
            raise HTTPException(
                status_code=404,
                detail=f"Solution with name '{cleaned_solution_name}' not found"
            )
        solution_id = db_solution.solution_id

    packages, total = solution_package.get_multi_with_filters(
        db,
        skip=skip,
        limit=limit,
        solution_id=solution_id,
        name=name,
        version=version,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Enhance with solution names and model associations
    for package in packages:
        # Get solution name if not already loaded
        if not db_solution or package.solution_id != db_solution.solution_id:
            pkg_solution = solution.get_by_id(db, solution_id=package.solution_id)
            package.solution_name = pkg_solution.name if pkg_solution else None
        else:
            package.solution_name = db_solution.name
        
        # Get model associations
        associations = solution_package.get_model_associations(db, package_id=package.package_id)
        package.model_associations = [
            {
                "model_id": str(assoc.model_id)
            }
            for assoc in associations
        ]
    
    return SolutionPackageListResponse(
        total=total,
        packages=packages
    )


@router.get("/{package_id}", response_model=SolutionPackageSchema)
def get_package(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get a specific solution package by ID.
    
    **Permissions**: All authenticated users
    """
    db_package = solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Get solution name
    db_solution = solution.get_by_id(db, solution_id=db_package.solution_id)
    db_package.solution_name = db_solution.name if db_solution else None
    
    # Get model associations
    associations = solution_package.get_model_associations(db, package_id=package_id)
    db_package.model_associations = [
        {
            "model_id": str(assoc.model_id)
        }
        for assoc in associations
    ]
    
    return db_package


@router.put("/{package_id}", response_model=SolutionPackageSchema)
def update_package(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    package_in: SolutionPackageUpdate,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> Any:
    """
    Update a solution package (description and status only).
    
    **Permissions**: Admin and Engineer only
    """
    db_package = solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Update the package
    db_package = solution_package.update(db, db_obj=db_package, obj_in=package_in)
    
    # Log the update
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.PACKAGE_UPDATE,
        resource_type=AuditLogResourceType.SOLUTION_PACKAGE,
        resource_id=str(package_id),
        details={
            "updated_fields": package_in.dict(exclude_unset=True)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return db_package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
    delete_s3_file: bool = Query(False, description="Also delete the S3 file")
) -> None:
    """
    Delete a solution package.
    
    **Permissions**: Admin only
    **Note**: This will also remove all model associations
    """
    db_package = solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Delete S3 file if requested
    if delete_s3_file:
        solution_package_s3_manager.delete_package_file(db_package.s3_key)
    
    # Delete the package (this also deletes associations)
    solution_package.delete_package(db, package_id=package_id)
    
    # Log the deletion
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.PACKAGE_DELETE,
        resource_type=AuditLogResourceType.SOLUTION_PACKAGE,
        resource_id=str(package_id),
        details={
            "package_name": db_package.name,
            "version": db_package.version,
            "s3_file_deleted": delete_s3_file
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"Deleted package: {package_id}")


@router.get("/{package_id}/download-url", response_model=PackageDownloadUrlResponse)
def get_package_download_url(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration in seconds")
) -> Any:
    """
    Generate a presigned download URL for a package.
    
    **Permissions**: All authenticated users
    **Returns**: Presigned URL valid for the specified duration
    """
    db_package = solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Generate download URL
    download_url = solution_package_s3_manager.generate_download_url(
        s3_key=db_package.s3_key,
        expires_in=expires_in,
        filename=f"{db_package.name}_v{db_package.version}.tar.gz"
    )
    
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    return PackageDownloadUrlResponse(
        package_id=package_id,
        download_url=download_url,
        expires_in=expires_in,
        expires_at=expires_at
    )


@router.post("/{package_id}/associate-model", response_model=dict)
def associate_package_with_model(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    association: PackageModelAssociationCreate,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> Any:
    """
    Associate an AI model with a solution package.
    
    **Permissions**: Admin and Engineer only
    """
    # Verify package exists
    db_package = solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Verify model exists
    db_model = ai_model.get_by_id(db, model_id=association.model_id)
    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )
    
    # Create association
    result = solution_package.associate_with_model(
        db,
        package_id=package_id,
        model_id=association.model_id
    )
    
    # Log the action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="PACKAGE_MODEL_ASSOCIATE",
        resource_type="SOLUTION_PACKAGE",
        resource_id=str(package_id),
        details={
            "model_id": str(association.model_id)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"message": "Model associated successfully"}


@router.delete("/{package_id}/dissociate-model/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def dissociate_package_from_model(
    *,
    db: Session = Depends(deps.get_db),
    package_id: uuid.UUID,
    model_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> None:
    """
    Remove an AI model association from a solution package.
    
    **Permissions**: Admin and Engineer only
    """
    success = solution_package.remove_model_association(
        db,
        package_id=package_id,
        model_id=model_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Association not found"
        )
    
    # Log the action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="PACKAGE_MODEL_DISSOCIATE", 
        resource_type="SOLUTION_PACKAGE",
        resource_id=str(package_id),
        details={
            "model_id": str(model_id)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )