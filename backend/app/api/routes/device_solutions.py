from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import device_solution, device, solution, customer_solution
from app.models import User, UserRole, DeviceSolution, Device, Customer
from app.schemas.device_solution import (
    DeviceSolution as DeviceSolutionSchema,
    DeviceSolutionCreate,
    DeviceSolutionUpdate,
    DeviceSolutionDetailView
)
from app.utils.audit import log_action
from app.utils.logger import get_logger
import uuid

logger = get_logger("api.device_solutions")

router = APIRouter()

@router.post("", response_model=DeviceSolutionSchema)
def deploy_solution_to_device(
    *,
    db: Session = Depends(deps.get_db),
    solution_in: DeviceSolutionCreate,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Deploy a solution to a device.
    """
    # Get the device
    db_device = device.get_by_id(db, device_id=solution_in.device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Check if user has access to this device
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to deploy solutions to this device"
            )

    
    # Get the solution
    db_solution = solution.get_by_id(db, solution_id=solution_in.solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )

    
    # Check if customer has access to this solution
    if not customer_solution.check_customer_has_access(
        db, customer_id=db_device.customer_id, solution_id=solution_in.solution_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Customer does not have access to this solution"
        )

    
    # Check if solution is compatible with device
    if db_device.device_type.value not in db_solution.compatibility:
        raise HTTPException(
            status_code=400,
            detail=f"Solution {db_solution.name} is not compatible with device type {db_device.device_type.value}"
        )

    # Check if solution is already deployed
    existing_deployment = device_solution.get_by_device_and_solution(
        db, device_id=db_device.device_id, solution_id=db_solution.solution_id
    )

    if existing_deployment:
        raise HTTPException(
            status_code=400,
            detail=f"Solution {db_solution.name} is already deployed to this device"
        )

    # Check if ANY solution is already deployed to this device
    existing_solutions = device_solution.get_by_device(db, device_id=db_device.device_id)
    if existing_solutions and len(existing_solutions) > 0:
        existing_solution_names = []
        for existing_sol in existing_solutions:
            sol = solution.get_by_id(db, solution_id=existing_sol.solution_id)
            existing_solution_names.append(sol.name)
        
        raise HTTPException(
            status_code=400,
            detail=f"Device already has solution(s) deployed: {', '.join(existing_solution_names)}. Please remove existing solutions before deploying a new one."
        )


    # Check if customer has reached their license limit
    current_count = customer_solution.count_deployed_devices(
        db, customer_id=db_device.customer_id, solution_id=db_solution.solution_id
    )

    customer_solution_license = customer_solution.get_by_customer_and_solution(
        db, customer_id=db_device.customer_id, solution_id=db_solution.solution_id
    )

    if current_count >= customer_solution_license.max_devices:
        raise HTTPException(
            status_code=400,
            detail=f"Customer has reached maximum number of devices ({customer_solution_license.max_devices}) for this solution"
        )
    
    # Create the deployment
    new_deployment = device_solution.create(db, obj_in=solution_in)

    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_DEPLOYMENT",
        resource_type="DEVICE_SOLUTION",
        resource_id=str(new_deployment.id),
        details={
            "device_id": str(db_device.device_id),
            "solution_id": str(db_solution.solution_id),
            "device_name": db_device.name,
            "solution_name": db_solution.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Here you would typically start the actual deployment process
    # This could be a background task to push the solution to the device
    
    return new_deployment


@router.get("/device/{device_id}", response_model=List[DeviceSolutionDetailView])
def get_device_solutions(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all solutions deployed to a device.
    In practice, a device can only have one solution deployed at a time.
    """
    # Get the device
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Check if user has access to this device
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view solutions for this device"
            )
    
    # Get the solutions
    device_solutions = device_solution.get_by_device(db, device_id=device_id)

    # Enhance with solution details
    result = []
    for ds in device_solutions:
        sol = solution.get_by_id(db, solution_id=ds.solution_id)
        result.append({
            **ds.__dict__,
            "solution_name": sol.name,
            "solution_description": sol.description
        })
    
    return result



@router.put("/device/{device_id}", response_model=DeviceSolutionDetailView)
def update_device_solution_by_device_id(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    solution_in: DeviceSolutionUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Update a solution deployment by device ID.
    """
    # Get the deployment
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Check if user has access to this device
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update solutions for this device"
            )

    
    # Get the solution deployment
    device_solutions = device_solution.get_by_device(db, device_id=device_id)

    if not device_solutions or len(device_solutions) == 0:
        raise HTTPException(
            status_code=404,
            detail="No solution deployed on this device"
        )
    
    # Get the deployment
    ds = device_solutions[0]

    # Update the deployment using the original update function logic
    updated_deployment = device_solution.update(
        db, db_obj=ds, obj_in=solution_in
    )

    sol = solution.get_by_id(db, solution_id=updated_deployment.solution_id)
    updated_deployment_dict = {
        **updated_deployment.__dict__,
        "solution_name": sol.name,
        "solution_description": sol.description
    }


    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_UPDATE",
        resource_type="DEVICE_SOLUTION",
        resource_id=str(ds.id),
        details={
            "device_id": str(device_id),
            "updated_fields": [k for k, v in solution_in.dict(exclude_unset=True).items() if v is not None]
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return updated_deployment_dict

@router.delete("/device/{device_id}", response_model=DeviceSolutionSchema)
def remove_solution_from_device(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
    request: Request,
) -> Any:
    """
    Remove any solution deployed on a device.
    After removal, a different solution can be deployed to the device.
    """
    # Get the device
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    # Get the solution deployment
    device_solutions = device_solution.get_by_device(db, device_id=device_id)
    
    if not device_solutions or len(device_solutions) == 0:
        raise HTTPException(
            status_code=404,
            detail="No solution deployed on this device"
        )
    # Get the deployment
    ds = device_solutions[0]
    

    # Get the solution for logging
    db_solution = solution.get_by_id(db, solution_id=ds.solution_id)

    # Remove the deployment
    removed_deployment = device_solution.remove(db, id=ds.id)

    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_REMOVAL",
        resource_type="DEVICE_SOLUTION",
        resource_id=str(ds.id),
        details={
            "device_id": str(db_device.device_id),
            "device_name": db_device.name,
            "solution_id": str(db_solution.solution_id),
            "solution_name": db_solution.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return removed_deployment


@router.get("/current/device/{device_id}", response_model=Optional[DeviceSolutionDetailView])
def get_current_device_solution(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the currently deployed solution for a device.
    Returns null if no solution is deployed.
    """
    # Get the device
    db_device = device.get_by_id(db, device_id=device_id)
    if not db_device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    
    # Check if user has access to this device
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if db_device.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view solutions for this device"
            )
    
    # Get the solution deployment (should be at most one with our business rules)
    device_solutions = device_solution.get_by_device(db, device_id=device_id)
    
    if not device_solutions or len(device_solutions) == 0:
        return None
    
    # Get the first (and should be only) solution
    ds = device_solutions[0]
    sol = solution.get_by_id(db, solution_id=ds.solution_id)
    
    # Create a proper DeviceSolutionDetailView object
    detail_view = {
        "id": ds.id,
        "device_id": ds.device_id,
        "solution_id": ds.solution_id,
        "status": ds.status,
        "configuration": ds.configuration,
        "version_deployed": ds.version_deployed,
        "last_update": ds.last_update,
        "created_at": ds.created_at,
        "updated_at": ds.updated_at,
        "solution_name": sol.name,
        "solution_description": sol.description
    }
    
    return detail_view

@router.get("/solution/{solution_id}", response_model=List[DeviceSolutionDetailView])
def get_devices_by_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all devices that are using a specific solution with joined data.
    - Admins and Engineers can see all devices
    - Customer users can only see devices from their customer
    """
    # Check if solution exists
    sol = solution.get_by_id(db, solution_id=solution_id)
    if not sol:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Build an efficient query with joins
    query = (
        db.query(
            DeviceSolution,
            Device.name.label("device_name"),
            Device.location.label("device_location"),
            Device.customer_id,
            Customer.name.label("customer_name"),
        )
        .join(Device, DeviceSolution.device_id == Device.device_id)
        .join(Customer, Device.customer_id == Customer.customer_id)
        .filter(DeviceSolution.solution_id == solution_id)
    )
    
    # Filter based on user role
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        # Get the user's customer_id
        if not current_user.customer_id:
            return []
        
        # Add filter for customer
        query = query.filter(Device.customer_id == current_user.customer_id)
    
    # Execute the query
    results = query.all()
    
    # Process results into response objects
    response_data = []
    for result in results:
        ds = result[0]  # DeviceSolution object
        device_name = result[1]
        device_location = result[2]
        customer_id = result[3]
        customer_name = result[4]
        
        detail_view = {
            "id": ds.id,
            "device_id": ds.device_id,
            "device_name": device_name,
            "device_location": device_location,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "solution_id": ds.solution_id,
            "status": ds.status,
            "configuration": ds.configuration,
            "version_deployed": ds.version_deployed,
            "last_update": ds.last_update,
            "created_at": ds.created_at,
            "updated_at": ds.updated_at,
            "solution_name": sol.name,
            "solution_description": sol.description,
            "metrics": ds.metrics if hasattr(ds, "metrics") else None
        }
        
        response_data.append(detail_view)
    
    return response_data