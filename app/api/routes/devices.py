from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device, customer, solution, device_solution, customer_solution
from app.models import User, UserRole, DeviceStatus, Device as DeviceModel
from app.schemas.device import (
    Device as DeviceSchema,
    DeviceCreate,
    DeviceProvisionResponse,
    DeviceUpdate,
    DeviceAdminView,
    DeviceWithCustomerView,
    DeviceStatusInfo,
    DeviceBatchStatusRequest
)
from app.utils.audit import log_action
from app.utils.aws_iot import iot_core
from app.utils.logger import get_logger
from app.core.config import settings
from botocore.exceptions import NoCredentialsError, ClientError
from app.schemas.audit import AuditLogActionType, AuditLogResourceType
from app.utils.aws_iot_commands import iot_command_service
import uuid
import random
import boto3
import string

logger = get_logger("api.devices")

router = APIRouter()

# Dependency to get device and check access
def get_device_and_check_access(
    device_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> DeviceModel:
    """
    Dependency that gets a device by ID and verifies user access.
    Raises 404 if not found, 403 if not authorized.
    """
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this device")
            
    return db_device


@router.get("", response_model=List[DeviceWithCustomerView])
def get_devices(
    db: Session = Depends(deps.get_db),
    customer_id: Optional[uuid.UUID] = None,
    solution_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve devices with customer_name.
    - For admins and engineers: All devices or filtered by optional solution_id
    - For customers Only their customer's devices, optionally filtered by solution_id
    """
    # Validate solution_id if provided
    if solution_id:
        if not solution.get_by_id(db, solution_id=solution_id):
            raise HTTPException(status_code=404, detail="Solution not found")

    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Admins/Engineers can see all or filter by any customer/solution
        return device.get_with_customer_name_and_solution_filter(
            db, solution_id=solution_id, skip=skip, limit=limit
        )
    else:
        # Customer users can only see their own devices
        if not current_user.customer_id:
             return [] # Should not happen for customer users, but safe check

        if customer_id and current_user.customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify customer has access to the solution if filtering by it
        if solution_id and not customer_solution.check_customer_has_access(
            db, customer_id=current_user.customer_id, solution_id=solution_id
        ):
            raise HTTPException(status_code=403, detail="Not authorized to filter by this solution")
        
        return device.get_by_customer_with_name_and_solution_filter(
            db, customer_id=current_user.customer_id, solution_id=solution_id, skip=skip, limit=limit
        )

@router.post("", response_model=DeviceSchema)
def create_device(
    *,
    db: Session = Depends(deps.get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    Create a new device entry in the database (Admin or Engineer only).
    """
    if device_in.mac_address and device.get_by_mac_address(db, mac_address=device_in.mac_address):
        raise HTTPException(status_code=400, detail="A device with this MAC address already exists")

    if not customer.get_by_id(db, customer_id=device_in.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")

    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    device_name = f"D-{random_chars}"

    new_device = device.create(db, obj_in=device_in, device_name=device_name)

    log_action(
        db=db, user_id=current_user.user_id, action_type=AuditLogActionType.DEVICE_CREATE,
        resource_type=AuditLogResourceType.DEVICE, resource_id=str(new_device.device_id),
        details={"customer_id": str(new_device.customer_id), "device_type": new_device.device_type.value},
        ip_address=request.client.host, user_agent=request.headers.get("user-agent")
    )
    
    return new_device


@router.post("/{device_id}/provision", response_model=DeviceProvisionResponse)
def provision_device(
    *,
    db: Session = Depends(deps.get_db),
    db_device: DeviceModel = Depends(get_device_and_check_access),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    Provision a device in AWS IoT (Admin or Engineer only).
    """
    if db_device.thing_name:
        raise HTTPException(status_code=400, detail="Device is already provisioned")

    db_customer = customer.get_by_id(db, customer_id=db_device.customer_id)
    if not db_customer or not db_customer.iot_thing_group_name:
        raise HTTPException(status_code=400, detail="Customer does not have a valid IoT Thing Group")

    try:
        provision_info = iot_core.provision_device(
            device_id=db_device.device_id, thing_name=db_device.name,
            device_type=db_device.device_type.value, mac_address=db_device.mac_address,
            customer_group_name=db_customer.iot_thing_group_name
        )

        updated_device = device.update_cloud_info(
            db, device_id=db_device.device_id, **provision_info, status=DeviceStatus.PROVISIONED
        )

        log_action(
            db=db, user_id=current_user.user_id, action_type=AuditLogActionType.DEVICE_PROVISION,
            resource_type=AuditLogResourceType.DEVICE, resource_id=str(db_device.device_id),
            details={"thing_name": provision_info["thing_name"], "certificate_id": provision_info["certificate_id"]},
            ip_address=request.client.host, user_agent=request.headers.get("user-agent")
        )

        return DeviceProvisionResponse(
            device_id=str(db_device.device_id),
            thing_name=provision_info["thing_name"],
            certificate_url=provision_info["certificate_url"],
            private_key_url=provision_info["private_key_url"],
            status=updated_device.status
        )

    except Exception as e:
        logger.error(f"Error provisioning device {db_device.device_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error provisioning device: {str(e)}")


@router.get("/{device_id}", response_model=DeviceAdminView)
def get_device(
    db_device: DeviceModel = Depends(get_device_and_check_access)
) -> Any:
    """
    Get a specific device by ID. Access is handled by the dependency.
    """
    return db_device


@router.put("/{device_id}", response_model=DeviceSchema)
def update_device(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    device_in: DeviceUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Update a device.
    - Admins and Engineers can update any device
    - Customer admins can update only their customer's devices with limited fields
    - Customer users cannot update devices
    """
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    # Create a restricted update object based on device status and user role
    restricted_update = {}
        
    # These are safe to update for provisioned devices
    safe_fields = ["description", "location", "firmware_version", "latitude", "longitude"]

    # Admin/Engineer can update slightly more fields
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        safe_fields.extend(["ip_address", "configuration"]) 

    # Filter update to only include safe fields
    for field in safe_fields:
        if field in device_in.dict(exclude_unset=True):
            restricted_update[field] = getattr(device_in, field)

    # Critical fields that cannot be updated for provisioned devices
    forbidden_fields = ["device_type", "name", "thing_name", "thing_arn", "certificate_arn", "certificate_id"]
    for field in forbidden_fields:
        if field in device_in.dict(exclude_unset=True):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' cannot be updated after device provisioning"
            )

    # Check access permissions
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Admins and Engineers can update any device
        pass    
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admins can only update their customer's devices
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this device"
            )
    else:
        # Other users cannot update devices
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges to update devices"
        )

    # Create a proper update object from the restricted fields
    safe_update_obj = DeviceUpdate(**restricted_update)

    # Update device in database with restricted fields
    updated_device = device.update(db, db_obj=db_device, obj_in=safe_update_obj)

    # Log device update
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type=AuditLogActionType.DEVICE_UPDATE,
        resource_type=AuditLogResourceType.DEVICE,
        resource_id=str(device_id),
        details={"updated_fields": list(restricted_update.keys())},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_device


@router.delete("/{device_id}", response_model=DeviceSchema)
def delete_device(
    *,
    db: Session = Depends(deps.get_db),
    db_device: DeviceModel = Depends(get_device_and_check_access),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    バックエンド用
    Delete a device and remove from AWS IoT (Admin or Engineer only).
    """
    if db_device.thing_name and db_device.certificate_arn:
        try:
            iot_core.delete_thing_certificate(
                thing_name=db_device.thing_name, certificate_arn=db_device.certificate_arn
            )
        except Exception as e:
            logger.error(f"Error removing device {db_device.device_id} from AWS IoT: {str(e)}")
            # Continue with DB deletion even if cloud cleanup fails

    deleted_device = device.remove(db, id=db_device.device_id)
    
    log_action(
        db=db, user_id=current_user.user_id, action_type=AuditLogActionType.DEVICE_DELETE,
        resource_type=AuditLogResourceType.DEVICE, resource_id=str(db_device.device_id),
        details={"device_name": db_device.name, "customer_id": str(db_device.customer_id)},
        ip_address=request.client.host, user_agent=request.headers.get("user-agent")
    )
    
    return deleted_device


@router.post("/{device_id}/decommission", response_model=DeviceSchema)
def decommission_device(
    *,
    db: Session = Depends(deps.get_db),
    db_device: DeviceModel = Depends(get_device_and_check_access),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    Decommission a device (Admin or Engineer only).
    """
    if db_device.status == DeviceStatus.CREATED:
        raise HTTPException(status_code=400, detail="Device is not provisioned yet")
    
    decommissioned_device = device.decommission(db, device_id=db_device.device_id)
    
    log_action(
        db=db, user_id=current_user.user_id, action_type=AuditLogActionType.DEVICE_DECOMMISSION,
        resource_type=AuditLogResourceType.DEVICE, resource_id=str(db_device.device_id),
        ip_address=request.client.host, user_agent=request.headers.get("user-agent")
    )
    
    return decommissioned_device


@router.post("/{device_id}/activate", response_model=DeviceSchema)
def activate_device(
    *,
    db: Session = Depends(deps.get_db),
    db_device: DeviceModel = Depends(get_device_and_check_access),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    Activate a provisioned or inactive device (Admin or Engineer only).
    """
    activated_device = device.activate(db, device_id=db_device.device_id)
    
    log_action(
        db=db, user_id=current_user.user_id, action_type=AuditLogActionType.DEVICE_ACTIVATE,
        resource_type=AuditLogResourceType.DEVICE, resource_id=str(db_device.device_id),
        ip_address=request.client.host, user_agent=request.headers.get("user-agent")
    )
    
    return activated_device


@router.get("/compatible/solution/{solution_id}/customer/{customer_id}", response_model=List[DeviceSchema])
def get_compatible_devices_for_solution_by_customer(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    customer_id: uuid.UUID,
    available_only: bool = False,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get devices that are compatible with a specific solution for a customer.
    - Admins and Engineers can see devices for any customer
    - Customer users can only see devices from their own customer
    - If available_only is True, only returns devices that don't have a solution already deployed
    """
    # Get the solution
    db_solution = solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Check if customer exists
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    
    # Check permissions for customer users
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if current_user.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access devices from other customers"
            )
    
    # Get all devices for the customer
    customer_devices = device.get_by_customer(db, customer_id=customer_id)
    
    # Filter devices by compatibility with the solution
    compatible_devices = []
    for dev in customer_devices:
        # Check if device is compatible
        if dev.device_type.value in db_solution.compatibility:
            # If available_only is True, check if device already has a solution deployed
            if available_only:
                existing_solutions = device_solution.get_by_device(db, device_id=dev.device_id)
                if existing_solutions and len(existing_solutions) > 0:
                    continue  # Skip this device as it has a solution deployed
            compatible_devices.append(dev)
    
    return compatible_devices


@router.get("/{device_id}/image")
def get_device_image(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    solution: str,
    current_user: User = Depends(deps.get_current_active_user),
    timestamp: Optional[str] = None,  # Cache busting parameter
) -> Any:
    """
    Get the latest captured image for a device.
    
    - Admins and Engineers can access any device's image
    - Customer users can only access their customer's devices
    - Images are stored in S3 and served directly
    """
    # Get and validate device
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this device's images"
            )

    
    # Check if device is active/provisioned
    if db_device.status not in [DeviceStatus.ACTIVE, DeviceStatus.PROVISIONED]:
        raise HTTPException(
            status_code=400,
            detail=f"Device is not active (current status: {db_device.status.value})"
        )

    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        object_key = f"captures/{solution}/{db_device.name}/capture.jpg"

        try:
            response = s3_client.get_object(
                Bucket="cc-captured-images",
                Key=object_key
            )

            
            # Stream the image data
            image_data = response['Body'].read()
            
            # Determine content type
            content_type = response.get('ContentType', 'image/jpeg')

            # Return the image as a streaming response
            return Response(
                content=image_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(
                    status_code=404,
                    detail="No image found for this device. Try capturing a new image first."
                )
            elif error_code == 'NoSuchBucket':
                raise HTTPException(
                    status_code=500,
                    detail="Image storage bucket not found"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error retrieving image: {str(e)}"
                )
                
    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not configured"
        )
    except Exception as e:
        logger.error(f"Error retrieving image for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal error retrieving device image"
        )

@router.post("/batch-status", response_model=Dict[str, DeviceStatusInfo])
def get_batch_device_status(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: DeviceBatchStatusRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get status for multiple devices in a single request.
    Returns a dictionary with device_id as key and status info as value.
    """
    result = {}
    
    for device_id in batch_request.device_ids:
        try:
            # Get device from database
            db_device = device.get_by_id(db, device_id=uuid.UUID(device_id))
            if not db_device:
                result[str(device_id)] = DeviceStatusInfo(
                    device_id=str(device_id),
                    device_name="Unknown",
                    is_online=False,
                    error="Device not found"
                )
                continue
            
            # Check access permissions
            if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
                if db_device.customer_id != current_user.customer_id:
                    result[str(device_id)] = DeviceStatusInfo(
                        device_id=str(device_id),
                        device_name=db_device.name,
                        is_online=False,
                        error="Not authorized"
                    )
                    continue
            
            # Default offline status
            status_info = DeviceStatusInfo(
                device_id=str(device_id),
                device_name=db_device.name,
                is_online=False,
                last_seen=None
            )
            
            # If device is provisioned, check shadow
            if db_device.thing_name:
                try:
                    shadow_document = iot_command_service.get_device_shadow(db_device.thing_name)
                    if shadow_document:
                        state = shadow_document.get("state", {})
                        reported = state.get("reported", {})
                        app_status = reported.get("applicationStatus")

                        if app_status:
                            # Check if online (status is "running" and within 5 minutes)
                            try:
                                status_info.last_seen = app_status.get("timestamp")
                                if app_status.get("status", "").lower() == "online":
                                    status_info.is_online = True
                            except:
                                pass      
                except Exception as e:
                    logger.warning(f"Failed to get shadow for device {device_id}: {str(e)}")
            
            result[str(device_id)] = status_info
        except Exception as e:
            logger.error(f"Error processing device {device_id}: {str(e)}")
            result[str(device_id)] = DeviceStatusInfo(
                device_id=str(device_id),
                device_name="Unknown",
                is_online=False,
                error=f"Error: {str(e)}"
            )
    
    return result