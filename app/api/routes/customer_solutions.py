from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import customer_solution, customer, solution
from app.models import User, UserRole
from app.schemas.customer_solution import (
    CustomerSolution as CustomerSolutionSchema,
    CustomerSolutionCreate,
    CustomerSolutionUpdate,
    CustomerSolutionAdminView,
)
from app.utils.audit import log_action
from app.utils.logger import get_logger
import uuid
from datetime import date

logger = get_logger("api.customer_solutions")

router = APIRouter()


@router.get("", response_model=List[CustomerSolutionAdminView])
async def get_customer_solutions(
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: Optional[uuid.UUID] = None,
    solution_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
) -> Any:
    """
    Get all customer solutions (admin only).
    Filter by customer_id or solution_id if provided.
    """
    # If customer_id is provided, check if customer exists
    if customer_id:
        customer_obj = await customer.get_by_id(db, customer_id=customer_id)
        if not customer_obj:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )
    
    # If solution_id is provided, check if solution exists
    if solution_id:
        solution_obj = await solution.get_by_id(db, solution_id=solution_id)
        if not solution_obj:
            raise HTTPException(
                status_code=404,
                detail="Solution not found"
            )
    
    # Use the new efficient function to get results with a single query
    results = await customer_solution.get_customer_solutions_with_details(
        db, 
        customer_id=customer_id,
        solution_id=solution_id,
        skip=skip, 
        limit=limit
    )
    
    return results


@router.post("", response_model=CustomerSolutionSchema)
async def add_solution_to_customer(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_solution_in: CustomerSolutionCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Add a solution to a customer (admin only).
    """
    # Check if customer exists
    customer_obj = await customer.get_by_id(db, customer_id=customer_solution_in.customer_id)
    if not customer_obj:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    
    
    # Check if solution exists
    solution_obj = await solution.get_by_id(db, solution_id=customer_solution_in.solution_id)
    if not solution_obj:
        raise HTTPException(
            status_code=404,
            detail="Solution not found"
        )
    
    
    # Check if customer already has this solution
    existing = await customer_solution.get_by_customer_and_solution(
        db, 
        customer_id=customer_solution_in.customer_id, 
        solution_id=customer_solution_in.solution_id
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Customer already has access to solution {solution_obj.name}"
        )
    
    # Add the solution to the customer
    new_customer_solution = await customer_solution.create(db, obj_in=customer_solution_in)

    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SOLUTION_ADD",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(new_customer_solution.id),
        details={
            "customer_id": str(customer_obj.customer_id),
            "customer_name": customer_obj.name,
            "solution_id": str(solution_obj.solution_id),
            "solution_name": solution_obj.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_customer_solution


@router.get("/customer/{customer_id}/solution/{solution_id}", response_model=CustomerSolutionSchema)
async def get_specific_customer_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific solution access for a customer.
    - Admins and Engineers can see for any customer
    - Customer users can only see their own customer's solutions
    """
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if current_user.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access other customers' solutions"
            )
    
    # Get the specific customer solution
    cs = await customer_solution.get_by_customer_and_solution_enhanced(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Customer solution not found"
        )
    
    return cs


@router.put("/customer/{customer_id}/solution/{solution_id}", response_model=CustomerSolutionSchema)
async def update_specific_customer_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    customer_solution_in: CustomerSolutionUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Update a customer's solution access.
    """
    # Get the customer solution
    cs = await customer_solution.get_by_customer_and_solution(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Customer solution not found"
        )
    
    # Update the customer solution
    updated_cs = await customer_solution.update(
        db, db_obj=cs, obj_in=customer_solution_in
    )
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SOLUTION_UPDATE",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(cs.id),
        details={"updated_fields": [k for k, v in customer_solution_in.dict(exclude_unset=True).items() if v is not None]},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_cs


@router.post("/customer/{customer_id}/solution/{solution_id}/suspend", response_model=CustomerSolutionSchema)
async def suspend_specific_customer_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Suspend a customer's access to a solution.
    """
    # Get the customer solution
    cs = await customer_solution.get_by_customer_and_solution(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Customer solution not found"
        )
    
    # Suspend the customer solution
    suspended_cs = await customer_solution.suspend(db, id=cs.id)
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SOLUTION_SUSPEND",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(cs.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return suspended_cs

@router.post("/customer/{customer_id}/solution/{solution_id}/activate", response_model=CustomerSolutionSchema)
async def activate_specific_customer_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Activate a customer's access to a solution.
    """
    # Get the customer solution
    cs = await customer_solution.get_by_customer_and_solution(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Customer solution not found"
        )
    
    # Activate the customer solution
    activated_cs = await customer_solution.activate(db, id=cs.id)
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SOLUTION_ACTIVATE",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(cs.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return activated_cs


@router.delete("/customer/{customer_id}/solution/{solution_id}", response_model=CustomerSolutionSchema)
async def remove_specific_customer_solution(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    customer_id: uuid.UUID,
    solution_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Remove a solution from a customer.
    This will also check if the solution is deployed to any of the customer's devices.
    """
    # Get the customer solution
    cs = await customer_solution.get_by_customer_and_solution(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if not cs:
        raise HTTPException(
            status_code=404,
            detail="Customer solution not found"
        )
    
    # Check if solution is deployed to any devices
    deployed_devices_count = await customer_solution.count_deployed_devices(
        db, customer_id=customer_id, solution_id=solution_id
    )
    
    if deployed_devices_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove solution: it is currently deployed to {deployed_devices_count} device(s) belonging to this customer. Please remove the solution from all devices first."
        )
    
    # Remove the customer solution
    removed_cs = await customer_solution.remove(db, id=cs.id)
    
    # Log action
    await log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SOLUTION_REMOVE",
        resource_type="CUSTOMER_SOLUTION",
        resource_id=str(cs.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return removed_cs
