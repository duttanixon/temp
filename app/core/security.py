from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
from zoneinfo import ZoneInfo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None, role: Optional[str] = None
) -> str:
    if expires_delta:
        expire = datetime.now(ZoneInfo("Asia/Tokyo")) + expires_delta
    else:
        expire = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except Exception as e:
        return None

def is_token_expired(payload: Dict[str, Any]) -> bool:
    if not payload or "exp" not in payload:
        return True
    
    exp_timestamp = payload.get("exp")
    if not exp_timestamp:
        return True
        
    expiration_time = datetime.fromtimestamp(exp_timestamp, tz=ZoneInfo("Asia/Tokyo"))
    current_time = datetime.now(ZoneInfo("Asia/Tokyo"))
    
    # Check if token is expired or about to expire in the next 5 minutes
    return current_time >= expiration_time or \
           current_time + timedelta(minutes=5) >= expiration_time

def refresh_token(token: str) -> Optional[str]:
    """
    Validate the token and create a new one with extended expiration
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    # Even if not expired, we can refresh it
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if not user_id:
        return None
    
    # Create a new token with extended expiration
    new_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        role=role
    )
    
    return new_token

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)