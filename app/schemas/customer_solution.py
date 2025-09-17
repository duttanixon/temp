from typing import Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel

from app.models.customer_solution import LicenseStatus

# Base Customer Solution Schema (shared properties)
class CustomerSolutionBase(BaseModel):
    customer_id: UUID
    solution_id: UUID
    license_status: Optional[LicenseStatus] = LicenseStatus.ACTIVE
    expiration_date: Optional[date] = None
    configuration_template: Optional[Dict[str, Any]] = None
# Properties to receive on customer solution creation
class CustomerSolutionCreate(CustomerSolutionBase):
    pass


# Properties to receive on customer solution update
class CustomerSolutionUpdate(BaseModel):
    license_status: Optional[LicenseStatus] = None
    expiration_date: Optional[date] = None

# Properties to return to client
class CustomerSolution(CustomerSolutionBase):
    id: UUID
    solution_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Admin view with additional details
class CustomerSolutionAdminView(CustomerSolution):
    # Include solution details
    solution_version: Optional[str] = None
    # Count of devices using this solution
    devices_count: Optional[int] = None

    # Add customer name field
    customer_name: Optional[str] = None
    
    class Config:
        from_attributes = True