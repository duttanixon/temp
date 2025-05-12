from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import customer, user
from app.models.user import User, UserRole
from app.schemas.customer import (
    Customer as CustomerSchema,
    CustomerCreate,
    CustomerUpdate,
    CustomerAdminView,    
)

from app.utils.audit import log_action
from app.utils.logger import get_logger
import uuid

# Initialize logger
logger = get_logger("api.customers")

router = APIRouter()

@router.get("", response_model=List[CustomerAdminView])
def read_customers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve customers (admin only)
    """
    customers = customer.get_multi(db, skip=skip, limit=limit)
    return customers


@router.post(
        "",
        response_model=CustomerAdminView,
        responses={
            400: {"description": "Bad Request - Customer already exists or email already exists"},
            403: {"description": "Forbidden - Not enough privileges"}
        }
)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Create new customer (admin only)
    """
    logger.info(f"Creating new customer: {customer_in.name} by user: {current_user.email} (ID: {current_user.user_id})")
    existing_customer = customer.get_by_name(db, name=customer_in.name)
    if existing_customer:
        logger.warning(f"Customer creation failed - name already exists: {customer_in.name}")
        raise HTTPException(
            status_code=400,
            detail="Customer already exists",
        )

    # Check for duplicate email
    existing_email = customer.get_by_email(db, contact_email=customer_in.contact_email)
    if existing_email:
        logger.warning(f"Customer creation failed - email already exists: {customer_in.contact_email}")
        raise HTTPException(
            status_code=400,
            detail="Customer with this email already exists",
        )
    
    new_customer = customer.create(db, obj_in=customer_in)
    logger.info(f"Customer created successfully: {new_customer.name} (ID: {new_customer.customer_id})")
    
    # Log customer creation
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_CREATE",
        resource_type="CUSTOMER",
        resource_id=str(new_customer.customer_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_customer

@router.get("/{customer_id}", response_model=CustomerAdminView)
def read_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_or_engineer_user),
) -> Any:
    """
    Get a specific customer by id (admin or engineer only)
    """
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )
    return db_customer


@router.put("/{customer_id}", response_model=CustomerAdminView)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    customer_in: CustomerUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Update a customer (admin only)
    """
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )
    
    # Check if customer name is being updated
    if customer_in.name is not None:
        # Validate that name is not empty
        if not customer_in.name.strip():
            raise HTTPException(
                status_code=422,
                detail="Customer name cannot be empty",
            )    

        # Check for duplicate name if name is being changed
        if customer_in.name != db_customer.name:
            existing_customer = customer.get_by_name(db, name=customer_in.name)
            if existing_customer:
                raise HTTPException(
                    status_code=400,
                    detail="Customer with this name already exists",
                )

    # Check if customer email is being updated
    if customer_in.contact_email is not None:
        # Validate that email is not empty
        if not customer_in.contact_email.strip():
            raise HTTPException(
                status_code=422,
                detail="Customer email cannot be empty",
            )
        
        # Check for duplicate email if email is being changed
        if customer_in.contact_email != db_customer.contact_email:
            existing_customer = customer.get_by_email(db, contact_email=customer_in.contact_email)
            if existing_customer:
                raise HTTPException(
                    status_code=400,
                    detail="Customer with this email already exists",
                )

    updated_customer = customer.update(db, db_obj=db_customer, obj_in=customer_in)
    
    # Log customer update
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_UPDATE",
        resource_type="CUSTOMER",
        resource_id=str(customer_id),
        details={"updated_fields": [k for k, v in customer_in.dict(exclude_unset=True).items() if v is not None]},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_customer


@router.post("/{customer_id}/suspend", response_model=CustomerAdminView)
def suspend_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Suspend a customer (admin only)
    """
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )
    
    suspended_customer = customer.suspend(db, customer_id=customer_id)
    
    # Log customer suspension
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_SUSPEND",
        resource_type="CUSTOMER",
        resource_id=str(customer_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return suspended_customer


@router.post("/{customer_id}/activate", response_model=CustomerAdminView)
def activate_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Activate a suspended customer (admin only)
    """
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )
    
    activated_customer = customer.activate(db, customer_id=customer_id)
    
    # Log customer activation
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_ACTIVATE",
        resource_type="CUSTOMER",
        resource_id=str(customer_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return activated_customer

@router.delete("/{customer_id}", response_model=CustomerAdminView)
def delete_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Delete a customer (admin only)
    Note - バックエンド利用のみ。
    """
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # Check if customer has any users
    user_list = user.get_by_customer(db, customer_id=customer_id)
    if user_list and len(user_list) > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete customer with associated users. Remove all users first.",
        )    
    deleted_customer = customer.remove(db, customer_id=customer_id)
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="CUSTOMER_DELETE",
        resource_type="CUSTOMER",
        resource_id=str(customer_id),
        details={"customer_name": db_customer.name},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return deleted_customer
    # todo: Check for other dependencies like devices or solutions
    # This would depend on specific data model