# implement authentication routes

from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token, verify_token, refresh_token, is_token_expired
from app.crud import user, password_reset_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import User as UserSchema, PasswordSet, TokenVerificationResponse, UserUpdate, ForgotPasswordRequest
from app.utils.audit import log_action
from app.utils.email import send_password_reset_email
from app.utils.logger import get_logger
from app.schemas.audit import AuditLogActionType

router = APIRouter()
logger = get_logger("auth")

@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(f"Login attempt for user: {form_data.username} from IP: {client_ip}")

    user_auth = user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user_auth:
        logger.warning(f"Failed login attempt for user: {form_data.username} from IP: {client_ip}")
        log_action(
            db=db,
            user_id=None,
            action_type=AuditLogActionType.LOGIN_FAILED,
            resource_type="USER",
            resource_id=form_data.username,
            details={"reason": "Invalid credentials"}
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active(user_auth):
        logger.warning(f"Inactive user login attempt: {form_data.username} from IP: {client_ip}")
        log_action(
            db=db,
            user_id=user_auth.user_id,
            action_type=AuditLogActionType.LOGIN_FAILED,
            resource_type="USER",
            resource_id=str(user_auth.user_id),
            details={"reason": "Inactive user"}
        )
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token = create_access_token(
        subject=str(user_auth.user_id), expires_delta=access_token_expires, role=user_auth.role.value
    )
    
    # Log successful login
    logger.info(f"Successful login for user: {form_data.username} (ID: {user_auth.user_id}) from IP: {client_ip}")
    log_action(
        db=db,
        user_id=user_auth.user_id,
        action_type=AuditLogActionType.LOGIN,
        resource_type="USER",
        resource_id=str(user_auth.user_id),
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/test-token", response_model=UserSchema)
def test_token(request: Request, current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"Token test by user: {current_user.email} (ID: {current_user.user_id}) from IP: {client_ip}")
    return current_user

@router.post("/refresh-token", response_model=Token)
def refresh_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    authorization: Optional[str] = Header(None)
) -> Any:
    """
    Refresh an access token before it expires
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.replace("Bearer ", "")
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Verify the token first
    payload = verify_token(token)
    if not payload:
        logger.warning(f"Token refresh failed - invalid token from IP: {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        logger.warning(f"Token refresh failed - no user ID in token from IP: {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check if token is close to expiration (otherwise no need to refresh)
    if not is_token_expired(payload):
        # Token is still valid for more than 5 minutes - return the same token
        return {"access_token": token, "token_type": "bearer"}

    # Generate a new token
    new_token = refresh_token(token)
    if not new_token:
        logger.warning(f"Token refresh failed for user ID: {user_id} from IP: {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Could not refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/set-password")
def set_password(
    *,
    db: Session = Depends(deps.get_db),
    password_data: PasswordSet,
) -> Any:
    """
    Set password using reset token
    """
    # Get token
    token_obj = password_reset_token.get_by_token(db, token=password_data.token)
    if not token_obj:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )
    
    # Get user
    user_obj = user.get_by_id(db, user_id=token_obj.user_id)
    if not user_obj:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Update password
    user_in = UserUpdate(password=password_data.new_password)
    updated_user = user.update(db, db_obj=user_obj, obj_in=user_in)
    
    # Mark token as used
    password_reset_token.mark_as_used(db, db_obj=token_obj)
    
    # Log password set action
    log_action(
        db=db,
        user_id=user_obj.user_id,
        action_type=AuditLogActionType.PASSWORD_CHANGE,
        resource_type="USER",
        resource_id=str(user_obj.user_id),
        details={"method": "password_reset_token"}
    )
    
    return {"message": "Password set successfully"}



@router.get("/verify-token/{token}", response_model=TokenVerificationResponse)
def verify_reset_token(
    *,
    db: Session = Depends(deps.get_db),
    token: str,
) -> Any:
    """
    Verify if a password reset token is valid
    """
    token_obj = password_reset_token.get_by_token(db, token=token)
    if not token_obj:
        return TokenVerificationResponse(valid=False)
    
    user_obj = user.get_by_id(db, user_id=token_obj.user_id)
    if not user_obj:
        return TokenVerificationResponse(valid=False)
    
    return TokenVerificationResponse(
        valid=True,
        email=user_obj.email,
        name=f"{user_obj.first_name or ''} {user_obj.last_name or ''}".strip() or user_obj.email
    )

@router.post("/forgot-password")
def forgot_password(
    *,
    db: Session = Depends(deps.get_db),
    request_data: ForgotPasswordRequest,
    request: Request,
) -> Any:
    """
    Request password reset via email
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(f"Password reset request for email: {request_data.email} from IP: {client_ip}")
    
    # Get user by email
    user_obj = user.get_by_email(db, email=request_data.email)
    
    # Always return success to prevent email enumeration
    # But only send email if user exists and is active
    if user_obj and user.is_active(user_obj):
        # Create password reset token
        reset_token = password_reset_token.create_token(db, user_id=user_obj.user_id)
        
        # Send password reset email
        email_sent = send_password_reset_email(
            email=user_obj.email,
            reset_token=reset_token.token
        )
        
        if email_sent:
            logger.info(f"Password reset email sent to user: {user_obj.email}")
            # Log the password reset request
            log_action(
                db=db,
                user_id=user_obj.user_id,
                action_type=AuditLogActionType.PASSWORD_RESET_REQUEST,
                resource_type="USER",
                resource_id=str(user_obj.user_id),
                ip_address=client_ip,
                user_agent=user_agent,
                details={"email": user_obj.email}
            )
        else:
            logger.error(f"Failed to send password reset email to: {user_obj.email}")
    else:
        # Log failed attempt only if user doesn't exist
        if not user_obj:
            logger.warning(f"Password reset request for non-existent email: {request_data.email} from IP: {client_ip}")
        else:
            logger.warning(f"Password reset request for inactive user: {request_data.email} from IP: {client_ip}")
    
    # Always return success to prevent email enumeration
    return {"message": "You will receive a password reset link shortly for valid email address."}