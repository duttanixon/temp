from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models import customer
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole, UserStatus 

# Base User Schema (shared properties)
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    customer_id: Optional[UUID] = None

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str
    email: EmailStr
    role: UserRole
    customer_id: Optional[UUID] = None


# Properties to receive on user update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[UserStatus] = None
    role: Optional[UserRole] = None
    customer_id: Optional[UUID] = None
    password: Optional[str] = None


# Properties to return to client
class User(UserBase):
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Properties for user profile (less sensitive)
class UserProfile(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Admin view of users (more detailed)
class UserAdminView(User):
    customer_id: Optional[UUID] = None

    class Config:
        from_attributes = True

# For changing password
class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str