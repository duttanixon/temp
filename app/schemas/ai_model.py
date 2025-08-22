# app/schemas/ai_model.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.ai_model import AIModelStatus


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class AIModelBase(BaseModel):
    """Base AI Model Schema (shared properties)"""
    name: str = Field(..., description="Name of the AI model")
    version: str = Field(..., description="Version of the model")
    description: Optional[str] = Field(None, description="Description of the model")
    status: Optional[AIModelStatus] = Field(default=AIModelStatus.ACTIVE, description="Status of the model")


class AIModelCreate(AIModelBase):
    """Properties to receive on model creation"""
    pass


class AIModelUpdate(BaseModel):
    """Properties to receive on model update"""
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AIModelStatus] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AIModel(AIModelBase):
    """Properties to return to client"""
    model_id: UUID
    s3_bucket: str
    s3_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIModelBasic(BaseModel):
    """Basic model info for references and lists"""
    model_id: UUID
    name: str
    version: str
    status: AIModelStatus

    class Config:
        from_attributes = True


class AIModelListResponse(BaseModel):
    """Response for paginated model list"""
    models: List[AIModel]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True


# ============================================================================
# DIRECT UPLOAD SCHEMAS
# ============================================================================

class UploadInitRequest(BaseModel):
    """Request to initiate a model upload"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the AI model")
    version: str = Field(..., min_length=1, max_length=50, description="Version of the model")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the model")
    status: Optional[AIModelStatus] = Field(AIModelStatus.IN_TESTING, description="Initial status")
    file_extension: str = Field(..., pattern=r"^\.[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)?$", description="File extension (e.g., .tar.gz, .h5)")
    file_size: int = Field(..., gt=0, le=1*1024*1024*1024, description="File size in bytes (max 1GB)")
    device_type: str = Field(..., description="Device type (e.g., CPU, GPU)")
    accelerator_type: str = Field(..., description="Accelerator type (e.g., NVIDIA, AMD)")



class UploadInitResponse(BaseModel):
    """Response with presigned upload URL and metadata"""
    upload_id: str = Field(..., description="Unique upload identifier")
    upload_url: str = Field(..., description="Presigned URL for direct S3 upload")
    upload_fields: Dict[str, str] = Field(..., description="Additional fields for multipart form upload")
    s3_key: str = Field(..., description="S3 key where file will be stored")
    expires_at: datetime = Field(..., description="When the upload URL expires")
    instructions: str = Field(..., description="Instructions for uploading")


class UploadCompleteRequest(BaseModel):
    """Request to complete the upload and create model record"""
    upload_id: str = Field(..., description="Upload ID from init response")
    s3_key: str = Field(..., description="S3 key where file was uploaded")
    name: str = Field(..., min_length=1, max_length=255, description="Model name")
    version: str = Field(..., min_length=1, max_length=50, description="Model version")
    description: Optional[str] = Field(None, max_length=1000, description="Model description")
    status: Optional[AIModelStatus] = Field(AIModelStatus.ACTIVE, description="Model status")
    file_size: int = Field(..., gt=0, description="Actual file size uploaded")


class BatchUploadVerifyRequest(BaseModel):
    """Request to verify a batch of uploads"""
    s3_keys: List[str] = Field(..., description="List of S3 keys to verify")

class ModelVerificationStatus(BaseModel):
    """Status for a single model verification"""
    s3_key: str
    exists: bool
    size: Optional[int] = None
    last_modified: Optional[datetime] = None

class BatchUploadVerifyResponse(BaseModel):
    """Response for a batch upload verification"""
    overall_status: str = Field(..., description="'SUCCESS' if all models exist, 'FAILED' otherwise")
    details: List[ModelVerificationStatus]



class UploadCancelRequest(BaseModel):
    """Request to cancel an upload"""
    upload_id: str = Field(..., description="Upload ID to cancel")
    s3_key: Optional[str] = Field(None, description="S3 key to delete")


class ModelDownloadUrlResponse(BaseModel):
    """Response with download URL"""
    model_id: UUID
    download_url: str
    expires_in: int
    expires_at: datetime