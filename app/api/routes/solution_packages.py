# app/api/routes/solution_packages.py
from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.async_session import AsyncSessionLocal
import uuid
import os
from datetime import datetime, timedelta

from app.api import deps
from app.crud import solution_package, solution, ai_model, device, job, device_solution
from app.models.solution_package import SolutionPackage
from app.models import User, JobType
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
    PackageModelAssociationCreate,
    DeployPackageRequest
)
from app.utils.solution_package_s3 import solution_package_s3_manager
from app.utils.aws_iot_commands import iot_command_service
from app.utils.ai_model_s3 import ai_model_s3_manager
from app.utils.util import check_device_access, validate_device_for_commands
from app.utils.audit import log_action
from app.utils.logger import get_logger
from app.utils.aws_iot_jobs import iot_jobs_service
from app.schemas.audit import AuditLogActionType, AuditLogResourceType
from app.core.config import settings
from app.schemas.job import JobCreate

logger = get_logger("api.solution_packages")

router = APIRouter()


# Helper function to generate package name based on solution name and device type
def _generate_package_name(solution_name: str, device_type: str) -> str:
    """Generates a package name in the format solution_name-device_type-package."""
    clean_solution_name = solution_name.lower().replace(" ", "_").replace("-", "_")
    clean_device_type = device_type.lower().replace(" ", "_").replace("-", "_")
    return f"{clean_solution_name}-{clean_device_type}-package"

# Helper function to handle version bumping
def _bump_version(version: str, major: bool, minor: bool, patch: bool) -> str:
    """Increments the version based on the specified booleans."""
    try:
        parts = version.split('.')
        current_major, current_minor, current_patch = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return "1.0.0"

    if major:
        current_major += 1
        current_minor = 0
        current_patch = 0
    elif minor:
        current_minor += 1
        current_patch = 0
    elif patch:
        current_patch += 1
    
    return f"{current_major}.{current_minor}.{current_patch}"

# ============================================================================
# DIRECT UPLOAD ENDPOINTS
# ============================================================================

@router.post("/upload/init", response_model=PackageUploadInitResponse)
async def initiate_package_upload(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
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
    db_solution = await solution.get_by_name(db, name=upload_request.solution_name)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail=f"Solution with name {upload_request.solution_name} not found"
        )
    
    # Generate package name based on solution name and device type
    package_name = _generate_package_name(upload_request.solution_name, upload_request.device_type)

    # Get the latest version of the package
    latest_package = await solution_package.get_latest_by_name_and_solution(
        db, 
        name=package_name, 
        solution_id=db_solution.solution_id
    )

    if latest_package:
        # Bump the version
        new_version = _bump_version(
            latest_package.version,
            upload_request.major,
            upload_request.minor,
            upload_request.patch
        )
    else:
        # First upload, start at 1.0.0
        new_version = "1.0.0"


    # Check for duplicate packages (in case of a race condition)
    existing_package = await solution_package.get_by_name_and_version(
        db, 
        name=package_name, 
        version=new_version,
        solution_id=db_solution.solution_id
    )
    if existing_package:
        raise HTTPException(
            status_code=400,
            detail=f"Package '{package_name}' version '{new_version}' already exists for this solution"
        )
    
    # Generate presigned upload URL
    try:
        upload_info = solution_package_s3_manager.generate_presigned_upload(
            solution_id=str(db_solution.solution_id),
            solution_name=str(db_solution.name),
            package_name=package_name,
            version=new_version,
            device_type=upload_request.device_type,
            accelarator_type=upload_request.accelarator_type,
            file_extension=upload_request.file_extension,
            file_size=upload_request.file_size,
            uploaded_by="system@cicd"
        )
        
        # Log the initiation
        await log_action(
            db=db,
            user_id=None,
            action_type=AuditLogActionType.PACKAGE_UPLOAD_INIT,
            resource_type=AuditLogResourceType.SOLUTION_PACKAGE,
            resource_id=upload_info["upload_id"],
            details={
                "action": "upload_initiated",
                "solution_name": str(db_solution.name),
                "package_name": package_name,
                "version": new_version,
                "file_size": upload_request.file_size
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(
            f"CI/CD system initiated package upload for {package_name} v{new_version}"
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
    db: AsyncSession = Depends(deps.get_async_db),
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
    db_solution = await solution.get_by_name(db, name=complete_request.solution_name)
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
    existing_package = await solution_package.get_by_name_and_version(
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
        
        db_package = await solution_package.create_with_s3_info(
            db,
            obj_in=package_in,
            s3_bucket=solution_package_s3_manager.bucket_name,
            s3_key=complete_request.s3_key
        )
        
        # Associate AI models if specified
        if complete_request.model_associations:
            for model_s3_key in complete_request.model_associations:
                # Verify model exists by s3_key
                db_model = await ai_model.get_by_s3_key(db, s3_key=model_s3_key)
                if db_model:
                    await solution_package.associate_with_model(
                        db,
                        package_id=db_package.package_id,
                        model_id=db_model.model_id,
                    )
                else:
                    logger.warning(f"Model with S3 key {model_s3_key} not found, skipping association")
        
        # Mark upload as complete
        solution_package_s3_manager.mark_upload_complete(complete_request.upload_id)
        
        # Log the action
        await log_action(
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
        db_solution = await solution.get_by_id(db, solution_id=db_package.solution_id)
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
async def list_packages(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    solution_name: Optional[str] = Query(None, description="Filter by solution name"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    version: Optional[str] = Query(None, description="Filter by version"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    device_id: Optional[str] = Query(None, description="Device ID to check for deployed package")
) -> Any:
    """
    List solution packages with optional filtering and sorting.
    If device_id is provided:
    1. Checks the AWS IoT Core classic shadow for the device
    2. Retrieves the deployed_id from the shadow
    3. Updates the device_solution table with the deployed package_id
    4. Includes the deployed_id in the response
        
    **Permissions**: All authenticated users
    """
    solution_id = None
    db_solution = None
    deployed_id = None

    # Handle device_id parameter if provided
    if device_id:
        try:
            # Convert string device_id to UUID
            device_uuid = uuid.UUID(device_id)
            
            # Get device from database
            db_device = await device.get_by_id(db, device_id=device_uuid)
            if db_device and db_device.thing_name:
                logger.info(f"Checking IoT shadow for device: {db_device.name} (thing_name: {db_device.thing_name})")
                
                # Get the classic shadow from IoT Core
                shadow_document = iot_command_service.get_device_shadow(db_device.thing_name)
                
                if shadow_document:
                    # Extract deployed_id from the shadow
                    reported_state = shadow_document.get("state", {}).get("reported", {})
                    shadow_deployed_id = reported_state.get("deployed_id")
                    
                    if shadow_deployed_id:
                        deployed_id = shadow_deployed_id
                        logger.info(f"Found deployed_id in shadow: {deployed_id}")
                        
                        # Try to parse as UUID to validate format
                        try:
                            deployed_package_uuid = uuid.UUID(shadow_deployed_id)
                            
                            # Check if this package exists in our database
                            deployed_package = await solution_package.get_by_id(db, package_id=deployed_package_uuid)
                            
                            if deployed_package:
                                # Update the device_solution table with the deployed package_id
                                device_solutions = await device_solution.get_by_device(db, device_id=device_uuid)
                                
                                if device_solutions and len(device_solutions) > 0:
                                    ds = device_solutions[0]
                                    
                                    # Update the package_id if it's different
                                    if str(ds.package_id) != shadow_deployed_id:
                                        logger.info(f"Updating device_solution package_id from {ds.package_id} to {deployed_package_uuid}")
                                        
                                        # Update the package_id in device_solution
                                        ds.package_id = deployed_package_uuid
                                        await db.commit()
                                        await db.refresh(ds)
                                        
                                        logger.info(f"Successfully updated device_solution with deployed package_id: {deployed_package_uuid}")
                                else:
                                    logger.warning(f"No device_solution found for device_id: {device_uuid}")
                            else:
                                logger.warning(f"Deployed package {deployed_package_uuid} not found in database")
                                
                        except ValueError as e:
                            logger.error(f"Invalid UUID format for deployed_id: {shadow_deployed_id}")
                    else:
                        logger.info("No deployed_id found in device shadow")
                else:
                    logger.warning(f"Could not retrieve shadow for device: {db_device.thing_name}")
            else:
                if not db_device:
                    logger.warning(f"Device not found: {device_id}")
                else:
                    logger.warning(f"Device {device_id} has no thing_name")
                    
        except ValueError as e:
            logger.error(f"Invalid device_id format: {device_id}")
        except Exception as e:
            logger.error(f"Error processing device shadow: {str(e)}")


    if solution_name:
        # Remove any surrounding quotes from solution_name
        print(f"Filtering by solution name: {solution_name}")
        cleaned_solution_name = solution_name.strip('"\'')
        db_solution = await solution.get_by_name(db, name=cleaned_solution_name)
        if not db_solution:
            raise HTTPException(
                status_code=404,
                detail=f"Solution with name '{cleaned_solution_name}' not found"
            )
        solution_id = db_solution.solution_id

    packages, total = await solution_package.get_multi_with_details(
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
        if package.solution:
            package.solution_name = package.solution.name
        
        # Get model associations from the eagerly loaded relationship
        model_associations_list = []
        if package.package_associations:
            for assoc in package.package_associations:
                if assoc.ai_model:
                    model_associations_list.append({
                        "model_id": str(assoc.ai_model.model_id),
                        "model_name": assoc.ai_model.s3_key.split('/')[-1]
                    })
        package.model_associations = model_associations_list

        # Add deployed_id to the package if it matches the current package
        if deployed_id and str(package.package_id) == deployed_id:
            package.deployed_id = deployed_id
    
    # Create response with deployed_id if available
    return SolutionPackageListResponse(
        total=total,
        packages=packages,
        skip=skip,
        limit=limit
    )


@router.get("/{package_id}", response_model=SolutionPackageSchema)
async def get_package(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    package_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get a specific solution package by ID.
    
    **Permissions**: All authenticated users
    """
    db_package = await solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Get solution name
    db_solution = await solution.get_by_id(db, solution_id=db_package.solution_id)
    db_package.solution_name = db_solution.name if db_solution else None
    
    # Get model associations
    associations = await solution_package.get_model_associations(db, package_id=package_id)
    db_package.model_associations = [
        {
            "model_id": str(assoc.model_id)
        }
        for assoc in associations
    ]
    
    return db_package


@router.put("/{package_id}", response_model=SolutionPackageSchema)
async def update_package(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    package_id: uuid.UUID,
    package_in: SolutionPackageUpdate,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> Any:
    """
    Update a solution package (description and status only).
    
    **Permissions**: Admin and Engineer only
    """
    db_package = await solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Update the package
    db_package = await solution_package.update(db, db_obj=db_package, obj_in=package_in)
    
    # Log the update
    await log_action(
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
async def delete_package(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
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
    db_package = await solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Delete S3 file if requested
    if delete_s3_file:
        solution_package_s3_manager.delete_package_file(db_package.s3_key)
    
    # Delete the package (this also deletes associations)
    await solution_package.delete_package(db, package_id=package_id)
    
    # Log the deletion
    await log_action(
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
async def get_package_download_url(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    package_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration in seconds")
) -> Any:
    """
    Generate a presigned download URL for a package.
    
    **Permissions**: All authenticated users
    **Returns**: Presigned URL valid for the specified duration
    """
    db_package = await solution_package.get_by_id(db, package_id=package_id)
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
async def associate_package_with_model(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
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
    db_package = await solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Verify model exists
    db_model = await ai_model.get_by_id(db, model_id=association.model_id)
    if not db_model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )
    
    # Create association
    result = await solution_package.associate_with_model(
        db,
        package_id=package_id,
        model_id=association.model_id
    )
    
    # Log the action
    await log_action(
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
async def dissociate_package_from_model(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    package_id: uuid.UUID,
    model_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request
) -> None:
    """
    Remove an AI model association from a solution package.
    
    **Permissions**: Admin and Engineer only
    """
    success = await solution_package.remove_model_association(
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
    await log_action(
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


@router.post("/{package_id}/deploy", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def deploy_solution_package(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    package_id: uuid.UUID, # Get package_id from path parameter
    deploy_request: DeployPackageRequest, # Use the new request schema
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    background_tasks: BackgroundTasks,
    request: Request,
) -> Any:
    """
    Deploy a solution package to specified devices using AWS IoT Core Jobs.

    This endpoint:
    1. Validates the package and targets
    2. Generate download URLs for package and associated models
    3. Creates an AWS IoT Core Job to deploy the package and models to target devices.
    """
    logger.info(f"Deployment request for package {package_id} to devices: {deploy_request.device_ids}")

    # 1. Validate Package ID and retrieve metadata
    db_package = await solution_package.get_by_id(db, package_id=package_id)
    if not db_package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    
    # Get associated solution name for logging/S3 key generation if needed
    db_solution = await solution.get_by_id(db, solution_id=db_package.solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Associated solution not found for this package"
        )
    
    # 2. Generate Download Links
    job_document_steps = []
    installation_script_args = [str(db_package.package_id)]  # Start with package ID as first arg
    # Add step for package file download
    package_filename = f"{db_package.name}_{db_package.version}.zip".replace(" ", "_")
    package_local_path = f"/tmp/{package_filename}"
    package_download_url = solution_package_s3_manager.generate_download_url(
        s3_key=db_package.s3_key,
        expires_in=3600 * 24, # URL valid for 24 hours for job execution
        filename=package_filename
    )

    job_document_steps.append({
        "action": {
            "name": f"Download Package {db_package.name}_{db_package.version}",
            "type": "runHandler",
            "input": {
                "handler": "software_dl.sh", 
                "args": [
                    package_download_url,
                    package_local_path
                ],
                "path": deploy_request.path_to_handler
            },
            "runAsUser": deploy_request.run_as_user
        }
    })

    installation_script_args.append(package_local_path)

    # Add steps for associated model downloads
    model_associations = await solution_package.get_model_associations(db, package_id=package_id)
    for assoc in model_associations:
        db_model = await ai_model.get_by_id(db, model_id=assoc.model_id)
        if db_model:
            model_filename = os.path.basename(db_model.s3_key)
            model_local_path = f"/tmp/{model_filename}"

            model_download_url = ai_model_s3_manager.generate_download_url(
                s3_key=db_model.s3_key,
                expires_in=3600 * 24, # URL valid for 24 hours
                filename=model_filename
            )
            job_document_steps.append({
                "action": {
                    "name": f"Download Model {db_model.name}_{db_model.version}",
                    "type": "runHandler",
                    "input": {
                        "handler": "download_aimodel.sh",
                        "args": [
                            model_download_url,
                            model_local_path
                        ],
                        "path": deploy_request.path_to_handler
                    },
                    "runAsUser": deploy_request.run_as_user
                }
            })
            installation_script_args.append(model_local_path)
        else:
            logger.warning(f"Associated model {assoc.model_id} not found for package {package_id}. Skipping download step.")

    # Add final installation/setup step
    job_document_steps.append({
        "action": {
            "name": "Install and setup the application",
            "type": "runHandler",
            "input": {
                "handler": "install-application.sh", # Assuming this script handles installation
                "args": installation_script_args, # Pass any custom args
                "path": deploy_request.path_to_handler
            },
            "runAsUser": deploy_request.run_as_user
        }
    })

    # Create the job document
    job_document = {
        "version": "1.0",
        "steps": job_document_steps
    }


    # 3. AWS IoT Core Job Creation (as a background task for multiple devices)
    
    # Inner function for the background task
    async def create_deployment_jobs_task(
        package: SolutionPackage,
        target_device_ids: List[uuid.UUID],
        job_doc: Dict[str, Any],
        user: User,
        ip: str,
        ua: str,
    ):
        logger.info(f"Background task started: Creating deployment jobs for package {package.package_id} on {len(target_device_ids)} devices.")
        success_count = 0
        async with AsyncSessionLocal() as db_session:
            try:
                for device_id in target_device_ids:
                    try:
                        db_device = await device.get_by_id(db_session, device_id=device_id)
                        if not db_device:
                            logger.warning(f"Device {device_id} not found. Skipping job creation.")
                            continue
                        
                        await check_device_access(user, db_device, action="deploy packages to")
                        thing_name = validate_device_for_commands(db_device)

                        # Create the IoT Job using the iot_jobs_service
                        aws_job_info = iot_jobs_service.create_package_deployment_job(
                            job_id_prefix=f"deploy-{package.name.replace(' ', '-')[:13]}-{package.version.replace('.', '-')[:13]}",
                            targets=[f"arn:aws:iot:{settings.AWS_REGION}:{settings.AWS_ACCOUNT_ID}:thing/{thing_name}"],
                            document=job_doc,
                            target_selection='SNAPSHOT',
                            description=f"Deploy package {package.name} v{package.version} to {thing_name}"
                        )

                        # Record job in our database
                        job_create_schema = JobCreate(
                            device_id=device_id,
                            job_type=JobType.PACKAGE_DEPLOYMENT,
                            parameters={
                                "package_id": str(package.package_id),
                                "package_name": package.name,
                                "package_version": package.version,
                                "job_document_steps": job_doc["steps"] # Store the steps for audit
                            }
                        )
                        db_job = await job.create_with_device_update(
                            db_session, obj_in=job_create_schema, job_id=aws_job_info["job_id"], user_id=user.user_id
                        )
                        db_job.aws_job_arn = aws_job_info.get("job_arn")
                        db_session.add(db_job)
                        await db_session.commit()

                        await log_action(
                            db=db_session, user_id=user.user_id, action_type=AuditLogActionType.JOB_CREATE,
                            resource_type=AuditLogResourceType.JOB, resource_id=str(db_job.id),
                            details={
                                "job_id": db_job.job_id,
                                "job_type": "PACKAGE_DEPLOYMENT",
                                "device_id": str(device_id),
                                "device_name": db_device.name,
                                "package_id": str(package.package_id),
                                "package_name": package.name,
                                "package_version": package.version
                            },
                            ip_address=ip, user_agent=ua
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create deployment job for device {device_id} and package {package.package_id}: {e}")
                        await db_session.rollback() # Rollback session on error for this device
            except Exception as e:
                await db_session.rollback()
                logger.error(f"Error in deployment task: {e}")
                raise
            finally:
                # Always close the session
                await db_session.close()
        logger.info(f"Background task finished: Successfully initiated {success_count}/{len(target_device_ids)} deployment jobs.")

    # Add the deployment task to background tasks
    background_tasks.add_task(
        create_deployment_jobs_task,
        package=db_package,
        target_device_ids=deploy_request.device_ids,
        job_doc=job_document,
        user=current_user,
        ip=request.client.host,
        ua=request.headers.get("user-agent"),
    )

    return {
        "message": f"Deployment of package {package_id} to {len(deploy_request.device_ids)} devices has been initiated.",
        "package_id": str(package_id),
        "devices_count": len(deploy_request.device_ids)
    }