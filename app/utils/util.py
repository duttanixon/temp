from app.models import User, UserRole, DeviceStatus
from fastapi import HTTPException

def check_device_access(
    current_user: User, db_device, action: str = "send commands to"
):
    """Helper function to check if user has access to device"""
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if (
            not current_user.customer_id
            or db_device.customer_id != current_user.customer_id
        ):
            raise HTTPException(
                status_code=403, detail=f"Not authorized to {action} this device"
            )
        
def validate_device_for_commands(db_device) -> str:
    """Validate device can receive commands and return thing_name"""
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if db_device.status not in [DeviceStatus.ACTIVE, DeviceStatus.PROVISIONED]:
        raise HTTPException(
            status_code=400,
            detail=f"Device is not active (current status: {db_device.status.value})",
        )

    if not db_device.thing_name:
        raise HTTPException(
            status_code=400, detail="Device is not provisioned in AWS IoT Core"
        )

    return db_device.thing_name