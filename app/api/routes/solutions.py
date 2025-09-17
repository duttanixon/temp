from typing import Any, List, Optional, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import solution, customer_solution, device, device_solution, customer
from app.models import User, UserRole, DeviceType
from app.schemas.solution import (
    Solution as SolutionSchema,
    SolutionCreate,
    SolutionUpdate,
    SolutionAdminView,
)
from app.schemas import CustomerBasic
from app.utils.audit import log_action
from app.utils.logger import get_logger
import uuid

logger = get_logger("api.solutions")

router = APIRouter()

@router.get("", response_model=List[SolutionSchema])
async def get_solutions(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    device_type: Optional[str] = None,
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
                solutions_list = await solution.get_compatible_with_device_type(
                    db, device_type=device_type, skip=skip, limit=limit
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid device type: {device_type}"
                )
        else:
            solutions_list = await solution.get_multi(db, skip=skip, limit=limit)
        
        return solutions_list

    # For Customer roles - return only solutions assigned to their customer
    else:
        if not current_user.customer_id:
            # Customer user without a customer_id shouldn't happen, but just in case
            return []
        # Get customer solutions first
        customer_solutions_list = await customer_solution.get_active_by_customer(
            db, customer_id=current_user.customer_id
        )
        
        # Extract solution IDs
        solution_ids = [cs.solution_id for cs in customer_solutions_list]
        
        if not solution_ids:
            return []

        
        # First build the base query for customer solutions
        base_query_solutions = await solution.get_by_ids(db, ids=solution_ids)

        solutions_list = []
        for sol_item in base_query_solutions:
            # Add device type filter if provided        
            if device_type:
                try:
                    DeviceType(device_type)
                    if not (sol_item.compatibility and device_type in sol_item.compatibility):
                        continue
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid device type: {device_type}"
                    )
            
            solutions_list.append(sol_item)
            
        return solutions_list[:limit]

@router.get("/admin", response_model=List[SolutionAdminView])
async def get_solutions_admin_view(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
) -> Any:
    """
    Retrieve solutions with additional admin details.
    Admin or Engineer only.
    """
    solutions_list = await solution.get_multi(db, skip=skip, limit=limit)
    # Enhance with usage counts
    enhanced_solutions = []
    for sol in solutions_list:
        enhanced_data = await solution.get_with_customer_count(db, solution_id=sol.solution_id)
        enhanced_solutions.append(enhanced_data)

    return enhanced_solutions


@router.post("", response_model=SolutionSchema)
async def create_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_in: SolutionCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Create a new solution.
    Admin only.
    """
    # Check if solution with this name already exists
    db_solution = await solution.get_by_name(db, name=solution_in.name)
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
    new_solution = await solution.create(db, obj_in=solution_in)
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_CREATE",
        resource_type="SOLUTION",
        resource_id=str(new_solution.solution_id),
        details={"name": new_solution.name},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_solution


@router.get("/available-customers", response_model=List[CustomerBasic])
async def get_available_customers(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_id: str,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get customers that are available to be assigned a specific solution
    (i.e., customers that do not already have this solution assigned).
    Admin only.
    """
    # Check if the solution exists
    try:
        # Convert string to UUID object
        solution_uuid = uuid.UUID(solution_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid solution ID format"
        )
    db_solution = await solution.get_by_id(db, solution_id=solution_uuid)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    # Get all customers
    all_customers = await customer.get_multi(db)

    # Get customer IDs that already have this solution
    assigned_customer_solutions = await customer_solution.get_by_solution(db, solution_id=solution_uuid)

    assigned_customer_ids = set(cs.customer_id for cs in assigned_customer_solutions)

    # Filter the customers list to exclude those that already have the solution assigned
    available_customers = [
        c for c in all_customers
        if c.customer_id not in assigned_customer_ids
    ]
    return available_customers


@router.get("/assigned-customers", response_model=List[CustomerBasic])
async def get_assigned_customers(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_id: str,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get customers that have already been assigned a specific solution.
    Admin only.
    """
    # Check if the solution exists
    try:
        # Convert string to UUID object
        solution_uuid = uuid.UUID(solution_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid solution ID format"
        )
    db_solution = await solution.get_by_id(db, solution_id=solution_uuid)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Query the customer_solutions table to find all active customer-solution 
    # assignments for this solution
    customer_solutions_list = await customer_solution.get_by_active_solution(db, solution_id=solution_uuid)
    
    customer_ids = [cs.customer_id for cs in customer_solutions_list]
    
    # If there are no assigned customers, return an empty list
    if not customer_ids:
        return []

    
    # Join with the customers table to get the customer names
    assigned_customers = await customer.get_by_ids(db, ids=customer_ids)
    
    return assigned_customers


@router.get("/{solution_id}", response_model=Union[SolutionSchema, SolutionAdminView])
async def get_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific solution by ID.
    - Admins and Engineers can access any solution
    - Customer users can only access solutions assigned to their customer
    """
    # Get the solution
    db_solution = await solution.get_by_id(db, solution_id=solution_id)
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
        has_access = await customer_solution.check_customer_has_access(
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
        return SolutionAdminView.model_validate(await solution.get_with_customer_count(db, solution_id=solution_id))

    # For regular users, return without the counts
    return SolutionSchema.model_validate(db_solution)


@router.put("/{solution_id}", response_model=SolutionSchema)
async def update_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_id: uuid.UUID,
    solution_in: SolutionUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Update a solution.
    Admin only.
    """
    db_solution = await solution.get_by_id(db, solution_id=solution_id)
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
        existing_solution = await solution.get_by_name(db, name=solution_in.name)
        if existing_solution:
            raise HTTPException(
                status_code=400,
                detail="Solution with this name already exists"
            )
        
    
    # Update the solution
    updated_solution = await solution.update(db, db_obj=db_solution, obj_in=solution_in)

    
    # Log action
    await log_action(
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

@router.get("/compatibility/device/{device_id}", response_model=List[SolutionSchema])
async def get_compatible_solutions_for_device(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    device_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get solutions compatible with a specific device and available to the customer.
    Note: A device can only have one solution deployed at a time.
    Returns empty list if the device already has a solution deployed.
    """
    db_device = await device.get_by_id(db, device_id=device_id)
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
    existing_solutions = await device_solution.get_by_device(db, device_id=device_id)
    if existing_solutions and len(existing_solutions) > 0:
        # If device already has a solution, return empty list
        return []
    
    # For admin/engineer, get all solutions compatible with this device type
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        return await solution.get_compatible_with_device_type(
            db, device_type=db_device.device_type.value
        )

    # For customer users, get solutions that are:
    # 1. Compatible with this device type
    # 2. Available to the customer
    # Get active customer solutions
    customer_solutions_list = await customer_solution.get_active_by_customer(
        db, customer_id=current_user.customer_id
    )

    # Extract solution IDs
    solution_ids = [cs.solution_id for cs in customer_solutions_list]
    
    if not solution_ids:
        return []

    # Get compatible solutions
    compatible_solutions = await solution.get_by_ids(db, ids=solution_ids)
    
    compatible = [
        sol for sol in compatible_solutions
        if db_device.device_type.value in sol.compatibility
    ]

    return compatible


@router.delete("/{solution_id}", response_model=SolutionSchema)
async def delete_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Delete a solution (Admin only).
    A solution cannot be deleted if it is assigned to any customer.
    """
    # Check if solution exists
    db_solution = await solution.get_by_id(db, solution_id=solution_id)
    if not db_solution:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    # Check if solution is assigned to any customers
    assigned_customers = await customer_solution.get_by_solution(db, solution_id=solution_id)
    if assigned_customers:
        customer_names = []
        for cs in assigned_customers:
            customer_obj = await customer.get_by_id(db, customer_id=cs.customer_id)
            if customer_obj:
                customer_names.append(customer_obj.name)
        
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete solution: it is currently assigned to {len(assigned_customers)} customer(s): {', '.join(customer_names)}. Please remove all customer assignments first."
        )
    
    # Delete the solution
    deleted_solution = await solution.remove(db, id=solution_id)
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="SOLUTION_DELETE",
        resource_type="SOLUTION",
        resource_id=str(solution_id),
        details={
            "solution_name": db_solution.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return deleted_solution
