from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import customer
from app.models.user import User, UserRole
from app.schemas.customer import (
    Customer as CustomerSchema,
    CustomerCreate,
    CustomerUpdate,
    CustomerAdminView,    
)

from app.utils.audit import log_action
import uuid

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


@router.post("", response_model=CustomerAdminView)
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
    existing_customer = customer.get_by_name(db, name=customer_in.name)
    if existing_customer:
        raise HTTPException(
            status_code=400,
            detail="A customer with this name already exists in the system",
        )
    
    new_customer = customer.create(db, obj_in=customer_in)
    
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