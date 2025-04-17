# implement authentication routes

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import User as UserSchema
from app.utils.audit import log_action

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_auth = user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user_auth:
        log_action(
            db=db,
            user_id=None,
            action_type="LOGIN_FAILED",
            resource_type="USER",
            resource_id=form_data.username,
            details={"reason": "Invalid credentials"}
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active(user_auth):
        log_action(
            db=db,
            user_id=user_auth.user_id,
            action_type="LOGIN_FAILED",
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
    log_action(
        db=db,
        user_id=user_auth.user_id,
        action_type="LOGIN",
        resource_type="USER",
        resource_id=str(user_auth.user_id)
    )
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/test-token", response_model=UserSchema)
def test_token(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user