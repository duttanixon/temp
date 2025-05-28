from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr

from app.models.customer import CustomerStatus


# Base Customer Schema (shared properties)
class CustomerBase(BaseModel):
    name: str
    contact_email: EmailStr
    address: Optional[str] = None
    status: Optional[CustomerStatus] = None


# Properties to receive on customer creation
class CustomerCreate(CustomerBase):
    pass


# Properties to receive on customer update
class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    address: Optional[str] = None
    status: Optional[CustomerStatus] = None


# Properties to return to client
class Customer(CustomerBase):
    customer_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Admin view of customer (more detailed)
class CustomerAdminView(Customer):
    iot_thing_group_name: Optional[str] = None
    iot_thing_group_arn: Optional[str] = None


    class Config:
        from_attributes = True

class CustomerBasic(BaseModel):
    """Basic customer information for list views"""
    customer_id: UUID
    name: str

    class Config:
        from_attributes = True