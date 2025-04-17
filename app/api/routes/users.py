from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import user, customer
from app.models.user import User, UserRole
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserAdminView,
)
from app.utils.audit import log_action
from app.utils.email import send_welcome_email
import uuid
import secrets
import string


router = APIRouter()

def generate_password() -> str:
    """Generate a random secure password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(12))


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None),
    email: Optional[EmailStr] = Body(None),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if first_name is not None:
        user_in.first_name = first_name
    if last_name is not None:
        user_in.last_name = last_name
    if email is not None:
        user_in.email = email
    updated_user = user.update(db, db_obj=current_user, obj_in=user_in)

    # Log user update
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_UPDATE",
        resource_type="USER",
        resource_id=str(current_user.user_id),
        details={"updated_fields": [k for k, v in user_in.dict(exclude_unset=True).items() if v is not None]}
    )
    
    return updated_user

@router.post("/password", response_model=UserSchema)
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    password_data: UserPasswordChange,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Change user password
    """
    if not user.authenticate(db, email=current_user.email, password=password_data.current_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    user_in = UserUpdate(password=password_data.new_password)
    updated_user = user.update(db, db_obj=current_user, obj_in=user_in)
    
    # Log password change
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="PASSWORD_CHANGE",
        resource_type="USER",
        resource_id=str(current_user.user_id)
    )
    
    return updated_user

# Admin routes

@router.get("", response_model=List[UserAdminView])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve users (admin only)
    """
    users = user.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("", response_model=UserAdminView)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Create new user (admin only)
    """
    existing_user = user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # If customer_id is provided, ensure it exists
    if user_in.customer_id:
        db_customer = customer.get_by_id(db, customer_id=user_in.customer_id)
        if not db_customer:
            raise HTTPException(
                status_code=404,
                detail="The customer with this ID does not exist",
            )
    
    # If password not provided, generate one
    if not hasattr(user_in, 'password') or not user_in.password:
        password = generate_password()
        user_in.password = password
        should_send_email = True
        print("here "*30)
    else:
        should_send_email = False
    
    new_user = user.create(db, obj_in=user_in)
    
    # Send welcome email with generated password
    if should_send_email:
        send_welcome_email(
            new_user.email, 
            f"{new_user.first_name or ''} {new_user.last_name or ''}".strip() or new_user.email,
            password
        )
    
    # Log user creation
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_CREATE",
        resource_type="USER",
        resource_id=str(new_user.user_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_user

@router.get("/{user_id}", response_model=UserAdminView)
def read_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get a specific user by id (admin only)
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return db_user

@router.put("/{user_id}", response_model=UserAdminView)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Update a user (admin only)
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # If customer_id is provided, ensure it exists
    if user_in.customer_id:
        db_customer = customer.get_by_id(db, customer_id=user_in.customer_id)
        if not db_customer:
            raise HTTPException(
                status_code=404,
                detail="The customer with this ID does not exist",
            )
    
    updated_user = user.update(db, db_obj=db_user, obj_in=user_in)
    
    # Log user update
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_UPDATE",
        resource_type="USER",
        resource_id=str(user_id),
        details={"updated_fields": [k for k, v in user_in.dict(exclude_unset=True).items() if v is not None]},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return updated_user

@router.post("/{user_id}/suspend", response_model=UserAdminView)
def suspend_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Suspend a user (admin only)
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # Cannot suspend yourself
    if db_user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot suspend yourself",
        )
    
    suspended_user = user.suspend(db, user_id=user_id)
    
    # Log user suspension
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_SUSPEND",
        resource_type="USER",
        resource_id=str(user_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return suspended_user


@router.post("/{user_id}/activate", response_model=UserAdminView)
def activate_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    request: Request,
) -> Any:
    """
    Activate a suspended user (admin only)
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    activated_user = user.activate(db, user_id=user_id)
    
    # Log user activation
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_ACTIVATE",
        resource_type="USER",
        resource_id=str(user_id),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return activated_user

# Customer admin routes
@router.get("/customer/{customer_id}", response_model=List[UserAdminView])
def read_users_by_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_customer_admin_user),
) -> Any:
    """
    Retrieve users for a specific customer (admin and customer admin)
    """
    # If user is customer admin, ensure they belong to the requested customer
    if current_user.role == UserRole.CUSTOMER_ADMIN and current_user.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access users from other customers",
        )
    
    users = user.get_by_customer(db, customer_id=customer_id)
    return users


@router.post("/customer/{customer_id}", response_model=UserAdminView)
def create_customer_user(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: uuid.UUID,
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_customer_admin_user),
    request: Request,
) -> Any:
    """
    Create new user for a specific customer (admin and customer admin)
    """
    # If user is customer admin, ensure they belong to the requested customer
    if current_user.role == UserRole.CUSTOMER_ADMIN and current_user.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to create users for other customers",
        )
    
    # Ensure customer exists
    db_customer = customer.get_by_id(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=404,
            detail="The customer with this ID does not exist",
        )
    
    # Check if user already exists
    existing_user = user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # Customer admin can only create customer users
    if current_user.role == UserRole.CUSTOMER_ADMIN and user_in.role not in [UserRole.CUSTOMER_USER, UserRole.CUSTOMER_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Customer admins can only create customer users or customer admins",
        )
    
    # Set customer ID
    user_in.customer_id = customer_id
    
    # If password not provided, generate one
    if not hasattr(user_in, 'password') or not user_in.password:
        password = generate_password()
        user_in.password = password
        should_send_email = True
    else:
        should_send_email = False
    
    new_user = user.create(db, obj_in=user_in)
    
    # Send welcome email with generated password
    if should_send_email:
        send_welcome_email(
            new_user.email, 
            f"{new_user.first_name or ''} {new_user.last_name or ''}".strip() or new_user.email,
            password
        )
    
    # Log user creation
    log_action(
        db=db,
        user_id=current_user.user_id,
        action_type="USER_CREATE",
        resource_type="USER",
        resource_id=str(new_user.user_id),
        details={"customer_id": str(customer_id)},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_user

