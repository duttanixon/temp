# implement authentication routes

from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token, verify_token, refresh_token, is_token_expired
import uuid
from app.crud import user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import User as UserSchema
from app.utils.audit import log_action
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

    # Log successful token refresh
    # logger.info(f"Token refreshed for user ID: {user_id} from IP: {client_ip}")
    # log_action(
    #     db=db,
    #     user_id=uuid.UUID(user_id),
    #     action_type="TOKEN_REFRESH",
    #     resource_type="USER",
    #     resource_id=user_id,
    #     ip_address=client_ip,
    #     user_agent=user_agent
    # )
    
    return {"access_token": new_token, "token_type": "bearer"}