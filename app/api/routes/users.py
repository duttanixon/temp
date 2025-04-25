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
    UserWithCustomerSchema
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


@router.get("/me", response_model=UserWithCustomerSchema)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user with their organization details (if applicable)
    """
    # Create a dictionary to hold the user data and customer info
    result = {
        **jsonable_encoder(current_user),
        "customer": None
    }
    if current_user.customer_id:
        customer_obj = customer.get_by_id(db, customer_id=current_user.customer_id)
        if customer_obj:
            result["customer"] = jsonable_encoder(customer_obj)
    return result

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
    customer_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users
    - For admins and engineers: All users or filtered by customer_id if provided
    - For customer admins: Only users from their own customer
    - For regular users: Not accessible
    """
    # Admin and Engineer can see all users or filter by customer
    if current_user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
        if customer_id:
            # Verify the customer exists
            db_customer = customer.get_by_id(db, customer_id=customer_id)
            if not db_customer:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found",
                )
            return user.get_by_customer(db, customer_id=customer_id)
        else:
            return user.get_multi(db, skip=skip, limit=limit)
        
    # Customer admins can only see users from their customer
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # If customer_id is provided, ensure it matches their own customer
        if customer_id and current_user.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access users from other customers",
            )
        return user.get_by_customer(db, customer_id=current_user.customer_id)

    # Other users don't have access
    else:
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
        )

@router.post("", response_model=UserAdminView)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
    customer_id: Optional[uuid.UUID] = None,
) -> Any:
    """
    Create new user.
    - For admins: Can create any user type for any customer
    - For customer admins: Can only create users for their own customer with limited roles
    - For regular users: Not accessible
    """
    # Check user's role for permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can create any user
        effective_customer_id = user_in.customer_id or customer_id
        
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admin can only create users for their own customer
        effective_customer_id = current_user.customer_id
        
        # Ensure they're not trying to create users for other customers
        if user_in.customer_id and user_in.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create users for other customers",
            )

        # Customer admin can only create customer users or customer admins
        if user_in.role not in [UserRole.CUSTOMER_USER, UserRole.CUSTOMER_ADMIN]:
            raise HTTPException(
                status_code=403,
                detail="Customer admins can only create customer users or customer admins",
            )
    else:
        # Other roles don't have access
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
        )

    # Check if user already exists
    existing_user = user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # Set customer ID if provided
    if effective_customer_id:
        # Verify customer exists
        db_customer = customer.get_by_id(db, customer_id=effective_customer_id)
        if not db_customer:
            raise HTTPException(
                status_code=404,
                detail="The customer with this ID does not exist",
            )
        user_in.customer_id = effective_customer_id
    
    # If password not provided, generate one
    should_send_email = False
    if not hasattr(user_in, 'password') or not user_in.password:
        password = generate_password()
        user_in.password = password
        should_send_email = True

    # Create the user
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
        details={"customer_id": str(new_user.customer_id) if new_user.customer_id else None},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_user

@router.get("/{user_id}", response_model=UserAdminView)
def read_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    - For admins: Can access any user
    - For customer admins: Can only access users from their own customer
    - For regular users: Not accessible
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    # Admins can see any user
    if current_user.role == UserRole.ADMIN:
        return db_user
    
    # Customer admins can only see users from their customer
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        if db_user.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access users from other customers",
            )
        return db_user
    # Other roles don't have access
    else:
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
        )

@router.put("/{user_id}", response_model=UserAdminView)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Update a user.
    - For admins: Can update any user
    - For customer admins: Can only update users from their own customer with limited roles
    - For regular users: Not accessible
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check permissions based on role
    if current_user.role == UserRole.ADMIN or current_user.role == UserRole.ENGINEER:
        # Admins can update any user
        if user_in.customer_id:
            # If customer_id is being changed, verify it exists
            db_customer = customer.get_by_id(db, customer_id=user_in.customer_id)
            if not db_customer:
                raise HTTPException(
                    status_code=404,
                    detail="The customer with this ID does not exist",
                )

    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admins can only update users from their own customer
        if db_user.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update users from other customers",
            )

        # Customer admins can't change user's customer
        if user_in.customer_id and user_in.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to change user's customer",
            )

        
        # Customer admins can only assign customer user or customer admin roles
        if user_in.role and user_in.role not in [UserRole.CUSTOMER_USER, UserRole.CUSTOMER_ADMIN]:
            raise HTTPException(
                status_code=403,
                detail="Customer admins can only assign customer user or customer admin roles",
            )
    
    else:
        # Other roles don't have permission
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
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
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Suspend a user.
    - For admins: Can suspend any user except themselves
    - For customer admins: Can only suspend users from their own customer
    - For regular users: Not accessible
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
    # Check role-based permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can suspend any user (except self)
        pass
    
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admin can only suspend users from their customer
        if db_user.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to suspend users from other customers",
            )
    
    else:
        # Other roles don't have permission
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
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
    current_user: User = Depends(deps.get_current_active_user),
    request: Request,
) -> Any:
    """
    Activate a suspended user.
    - For admins: Can activate any user
    - For customer admins: Can only activate users from their own customer
    - For regular users: Not accessible
    """
    db_user = user.get_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check role-based permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can activate any user
        pass
    
    elif current_user.role == UserRole.CUSTOMER_ADMIN:
        # Customer admin can only activate users from their customer
        if db_user.customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to activate users from other customers",
            )
    
    else:
        # Other roles don't have permission
        raise HTTPException(
            status_code=403,
            detail="Not enough privileges",
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