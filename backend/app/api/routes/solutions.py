from typing import Any, List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import solution, customer_solution, device, device_solution
from app.models import User, UserRole, DeviceType, Solution, SolutionStatus
from app.schemas.solution import (
    Solution as SolutionSchema,
    SolutionCreate,
    SolutionUpdate,
    SolutionAdminView,
)
from app.utils.audit import log_action
from app.utils.logger import get_logger
import uuid

logger = get_logger("api.solutions")

router = APIRouter()

@router.get("", response_model=List[SolutionSchema])
def get_solutions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    device_type: Optional[str] = None,
    active_only: bool = False,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve solutions based on user role:
    - Admins and Engineers: All solutions in the catalog
    - Customer Admins and Users: Only solutions assigned to their organization
    """
    # For Admin and Engineer roles - return all solutions with optional filters
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        if device_type:
            try:
                # Validate device type
                DeviceType(device_type)
                solutions_list = solution.get_compatible_with_device_type(
                    db, device_type=device_type, skip=skip, limit=limit
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid device type: {device_type}"
                )
        elif active_only:
            solutions_list = solution.get_active(db, skip=skip, limit=limit)
        else:
            solutions_list = solution.get_multi(db, skip=skip, limit=limit)

    # For Customer roles - return only solutions assigned to their customer
    else:
        if not current_user.customer_id:
            # Customer user without a customer_id shouldn't happen, but just in case
            return []
        # Get customer solutions first
        customer_solutions = customer_solution.get_active_by_customer(
            db, customer_id=current_user.customer_id
        )
        
        # Extract solution IDs
        solution_ids = [cs.solution_id for cs in customer_solutions]
        
        if not solution_ids:
            return []

        
        # First build the base query for customer solutions
        base_query = db.query(Solution).filter(Solution.solution_id.in_(solution_ids))

        # Add device type filter if provided        
        if device_type:
            try:
                DeviceType(device_type)
                base_query = base_query.filter(Solution.compatibility.contains([device_type]))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid device type: {device_type}"
                )
        
        # Add active status filter if requested
        if active_only:
            base_query = base_query.filter(Solution.status == SolutionStatus.ACTIVE)
        
        solutions_list = base_query.offset(skip).limit(limit).all()

    return solutions_list

@router.get("/admin", response_model=List[SolutionAdminView])
def get_solutions_admin_view(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
) -> Any:
    """
    Retrieve solutions with additional admin details.
    Admin or Engineer only.
    """
    solutions_list = solution.get_multi(db, skip=skip, limit=limit)
    # Enhance with usage counts
    enhanced_solutions = []
    for sol in solutions_list:
        enhanced_data = solution.get_with_customer_count(db, solution_id=sol.solution_id)
        enhanced_solutions.append(enhanced_data)

    return enhanced_solutions

@router.get("/available", response_model=List[SolutionSchema])
def get_available_solutions(
    db: Session = Depends(deps.get_db),
    device_type: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get available solutions for the current user's customer.
    This is a convenience endpoint for customer users.
    """
    if not current_user.customer_id:
        return []
    
    # Get active customer solutions
    customer_solutions = customer_solution.get_active_by_customer(
        db, customer_id=current_user.customer_id
    )

    # Extract solution IDs
    solution_ids = [cs.solution_id for cs in customer_solutions]

    if not solution_ids:
        return []

    # Get solutions with optional device type filter
    query = db.query(Solution).filter(
        Solution.solution_id.in_(solution_ids),
        Solution.status == SolutionStatus.ACTIVE
    )
    
    if device_type:
        try:
            DeviceType(device_type)
            query = query.filter(Solution.compatibility.contains([device_type]))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type: {device_type}"
            )
    
    return query.all()


@router.post("", response_model=SolutionSchema)
def create_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_in: SolutionCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Create a new solution.
    Admin only.
    """
    # Check if solution with this name already exists
    db_solution = solution.get_by_name(db, name=solution_in.name)
    if db_solution:
        raise HTTPException(
            status_code=400,
            detail="Solution with this name already exists"
        )
    
    # Validate device types in compatibility list
    for device_type in solution_in.compatibility:
        try:
            DeviceType(device_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type in compatibility list: {device_type}"
            )
    
    # Create the solution
    new_solution = solution.create(db, obj_in=solution_in)
    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_CREATE",
        resource_type="SOLUTION",
        resource_id=str(new_solution.solution_id),
        details={"name": new_solution.name, "version": new_solution.version},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_solution

@router.get("/{solution_id}", response_model=Union[SolutionSchema, SolutionAdminView])
def get_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific solution by ID.
    - Admins and Engineers can access any solution
    - Customer users can only access solutions assigned to their customer
    """
    # Get the solution
    db_solution = solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    # Check access permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        # For customer roles, check if they have access to this solution
        if not current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this solution"
            )
        
        # Check if customer has access to the solution
        has_access = customer_solution.check_customer_has_access(
            db, 
            customer_id=current_user.customer_id, 
            solution_id=solution_id
        )

        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this solution"
            )

    
    # For admins and engineers, include usage counts
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        return SolutionAdminView.parse_obj(solution.get_with_customer_count(db, solution_id=solution_id))

    # For regular users, return without the counts
    return SolutionSchema.from_orm(db_solution)


@router.put("/{solution_id}", response_model=SolutionSchema)
def update_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    solution_in: SolutionUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Update a solution.
    Admin only.
    """
    db_solution = solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )

    
    # If updating compatibility, validate device types
    if solution_in.compatibility:
        for device_type in solution_in.compatibility:
            try:
                DeviceType(device_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid device type in compatibility list: {device_type}"
                )

    
    # If updating name, check it doesn't conflict
    if solution_in.name and solution_in.name != db_solution.name:
        existing_solution = solution.get_by_name(db, name=solution_in.name)
        if existing_solution:
            raise HTTPException(
                status_code=400,
                detail="Solution with this name already exists"
            )
        
    
    # Update the solution
    updated_solution = solution.update(db, db_obj=db_solution, obj_in=solution_in)

    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_UPDATE",
        resource_type="SOLUTION",
        resource_id=str(solution_id),
        details={"updated_fields": [k for k, v in solution_in.dict(exclude_unset=True).items() if v is not None]},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_solution

@router.post("/{solution_id}/deprecate", response_model=SolutionSchema)
def deprecate_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Deprecate a solution.
    Admin only.
    """
    db_solution = solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    deprecated_solution = solution.deprecate(db, solution_id=solution_id)
    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_DEPRECATE",
        resource_type="SOLUTION",
        resource_id=str(solution_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return deprecated_solution

@router.post("/{solution_id}/activate", response_model=SolutionSchema)
def activate_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Activate a deprecated solution.
    Admin only.
    """
    db_solution = solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    activated_solution = solution.activate(db, solution_id=solution_id)
    
    # Log action
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_ACTIVATE",
        resource_type="SOLUTION",
        resource_id=str(solution_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return activated_solution

@router.get("/compatibility/device/{device_id}", response_model=List[SolutionSchema])
def get_compatible_solutions_for_device(
    *,
    db: Session = Depends(deps.get_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get solutions compatible with a specific device and available to the customer.
    Note: A device can only have one solution deployed at a time.
    Returns empty list if the device already has a solution deployed.
    """
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
                detail="Not authorized to access this device"
            )

    # Check if device already has a solution deployed
    existing_solutions = device_solution.get_by_device(db, device_id=device_id)
    if existing_solutions and len(existing_solutions) > 0:
        # If device already has a solution, return empty list
        return []
    
    # For admin/engineer, get all solutions compatible with this device type
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        return solution.get_compatible_with_device_type(
            db, device_type=db_device.device_type.value
        )

    # For customer users, get solutions that are:
    # 1. Compatible with this device type
    # 2. Available to the customer
    # Get active customer solutions
    customer_solutions = customer_solution.get_active_by_customer(
        db, customer_id=current_user.customer_id
    )

    # Extract solution IDs
    solution_ids = [cs.solution_id for cs in customer_solutions]
    
    if not solution_ids:
        return []

    # Get compatible solutions
    compatible_solutions = db.query(Solution).filter(
        Solution.solution_id.in_(solution_ids),
        Solution.status == SolutionStatus.ACTIVE,
        Solution.compatibility.contains([db_device.device_type.value])
    ).all()
    
    return compatible_solutions