# app/schemas/solution_package.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class SolutionPackageBase(BaseModel):
    """Base schema for solution package"""
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)


class SolutionPackageCreate(SolutionPackageBase):
    """Schema for creating a solution package"""
    solution_id: UUID
    s3_bucket: str
    s3_key: str


class SolutionPackageUpdate(BaseModel):
    """Schema for updating a solution package"""
    description: Optional[str] = Field(None, max_length=1000)


class SolutionPackage(SolutionPackageBase):
    """Schema for solution package response"""
    package_id: UUID
    solution_id: UUID
    s3_bucket: str
    s3_key: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Include related data
    solution_name: Optional[str] = None
    model_associations: Optional[List[Dict[str, Any]]] = None
    deployed_id: Optional[str] = None

    class Config:
        from_attributes = True


class SolutionPackageBasic(BaseModel):
    """Basic solution package info"""
    package_id: UUID
    name: str
    version: str
    created_at: datetime


# Upload schemas
class PackageUploadInitRequest(BaseModel):
    """Request to initiate package upload"""
    solution_name: str = Field(..., description="Solution name this package belongs to")
    description: Optional[str] = Field(None, max_length=1000, description="Package description")
    file_extension: str = Field(..., pattern=r"^\.[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?$", description="File extension (e.g., .tar.gz, .zip)")
    file_size: int = Field(..., gt=0, le=1*1024*1024*1024, description="File size in bytes (max 1GB)")
    device_type: str = Field(..., description="Target platform (e.g., linux/amd64, linux/arm64), raspberry pi, etc.")
    accelarator_type: str = Field(..., description="Accelerator type (e.g., nvidia, amd)")
    major: bool = Field(default=False, description="Increment major version")
    minor: bool = Field(default=False, description="Increment minor version")
    patch: bool = Field(default=True, description="Increment patch version")


class PackageUploadInitResponse(BaseModel):
    """Response with presigned upload URL and metadata"""
    upload_id: str = Field(..., description="Unique upload identifier")
    upload_url: str = Field(..., description="Presigned URL for direct S3 upload")
    upload_fields: Dict[str, str] = Field(..., description="Additional fields for multipart form upload")
    s3_key: str = Field(..., description="S3 key where file will be stored")
    expires_at: datetime = Field(..., description="When the upload URL expires")
    instructions: str = Field(..., description="Instructions for uploading")


class PackageUploadCompleteRequest(BaseModel):
    """Request to complete the upload and create package record"""
    upload_id: str = Field(..., description="Upload ID from init response")
    s3_key: str = Field(..., min_length=1, description="S3 key where file was uploaded")
    solution_name: str = Field(..., min_length=1, max_length=255, description="Solution name")
    name: str = Field(..., min_length=1, max_length=255, description="Package name")
    version: str = Field(..., min_length=1, max_length=50, description="Package version")
    description: Optional[str] = Field(None, max_length=1000, description="Package description")
    file_size: int = Field(..., gt=0, description="Actual file size uploaded")
    model_associations: Optional[List[str]] = Field(None, description="List of S3 keys of AI models to associate with this package")


class PackageUploadVerifyRequest(BaseModel):
    """Request to verify an upload"""
    upload_id: str = Field(..., description="Upload ID from init response")
    s3_key: str = Field(..., description="S3 key to verify")


class PackageUploadVerifyResponse(BaseModel):
    """Response after verifying upload"""
    upload_id: str
    s3_key: str
    file_exists: bool
    file_size: int
    last_modified: Optional[datetime]


class PackageUploadCancelRequest(BaseModel):
    """Request to cancel an upload"""
    upload_id: str = Field(..., description="Upload ID to cancel")
    s3_key: Optional[str] = Field(None, description="S3 key to delete")


class PackageDownloadUrlResponse(BaseModel):
    """Response with download URL"""
    package_id: UUID
    download_url: str
    expires_in: int
    expires_at: datetime


class SolutionPackageListResponse(BaseModel):
    """Response for listing packages"""
    total: int
    packages: List[SolutionPackage]
    skip: Optional[int] = None
    limit: Optional[int] = None


class PackageModelAssociation(BaseModel):
    """Schema for package-model association"""
    package_id: UUID
    model_id: UUID
    model_role: str = Field(..., description="Role of the model in this package (e.g., detection, classification)")
    
    class Config:
        from_attributes = True


class PackageModelAssociationCreate(BaseModel):
    """Create a package-model association"""
    model_id: UUID

class DeployPackageRequest(BaseModel):
    # package_id: UUID = Field(..., description="ID of the solution package to deploy")
    device_ids: List[UUID] = Field(..., min_items=1, description="List of device IDs to deploy the package to")
    path_to_handler: str = Field(default="/home/cybercore/jobs", description="Path to job handler on device")
    run_as_user: str = Field(default="cybercore", description="User to run the job as on device")
    install_script_args: Optional[List[str]] = Field(default=[], description="Arguments for the install-application.sh script")
