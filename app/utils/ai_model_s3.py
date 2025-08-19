# app/utils/ai_model_s3.py
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from app.core.config import settings
from app.utils.logger import get_logger
import json
# import redis
from contextlib import contextmanager
from zoneinfo import ZoneInfo

logger = get_logger("utils.ai_model_s3")


class AIModelS3Manager:
    """Manager for AI model S3 operations with direct upload support"""
    
    def __init__(self):
        """Initialize S3 client and Redis for upload tracking"""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = settings.AI_MODEL_BUCKET_NAME
        self.models_prefix = "ai-models"
        
        # Initialize Redis for tracking pending uploads (optional)
        try:
            # self.redis_client = redis.Redis(
            #     host=settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else 'localhost',
            #     port=settings.REDIS_PORT if hasattr(settings, 'REDIS_PORT') else 6379,
            #     db=settings.REDIS_DB if hasattr(settings, 'REDIS_DB') else 0,
            #     decode_responses=True
            # )
            # self.redis_available = self.redis_client.ping()
            raise Exception("Redis connection not implemented")  # Placeholder for Redis connection
            # logger.info("Redis connected for upload tracking")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory storage: {e}")
            self.redis_available = False
            self.pending_uploads = {}  # Fallback to in-memory storage
        
        logger.info("AI Model S3 Manager initialized")

    def generate_s3_key(
        self, 
        model_name: str,
        version: str, 
        device_type: str,
        accelerator_type: str, 
        file_extension: str
    ) -> str:
        """
        Generate S3 key for the model file
        """
        
        # Clean model name and version for use in path
        clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_name)
        clean_version = "".join(c if c.isalnum() or c in "-_." else "_" for c in version)
        
        s3_key = f"{device_type}/{accelerator_type}/{clean_name}_{clean_version}{file_extension}"
        return s3_key

    def generate_presigned_upload(
        self,
        model_name: str,
        version: str,
        device_type: str,
        accelerator_type: str,
        file_extension: str,
        file_size: int,
        uploaded_by: str,
        expires_in: int = 900  # 15 minutes default
    ) -> Dict[str, Any]:
        """
        Generate a presigned POST URL for direct S3 upload
        
        Args:
            model_name: Name of the AI model
            version: Version of the model
            file_extension: File extension
            file_size: Expected file size in bytes
            uploaded_by: Email of the uploader
            expires_in: URL expiration time in seconds
        
        Returns:
            Dictionary with upload URL, fields, and metadata
        """
        upload_id = str(uuid.uuid4())
        s3_key = self.generate_s3_key(
            model_name=model_name,
            version=version,
            device_type=device_type,
            accelerator_type=accelerator_type,
            file_extension=file_extension
        )
        expiration_time = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(seconds=expires_in)
        
        try:
            upload_timestamp = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            # Content type mapping
            content_types = {
                '.tar.gz': 'application/gzip',
                '.tar': 'application/x-tar',
                '.zip': 'application/zip',
                '.h5': 'application/octet-stream',
                '.pb': 'application/octet-stream',
                '.pth': 'application/octet-stream',
                '.pt': 'application/octet-stream',
                '.onnx': 'application/octet-stream',
                '.tflite': 'application/octet-stream',
                '.pkl': 'application/octet-stream',
                '.joblib': 'application/octet-stream',
                '.hef': 'application/octet-stream'
            }
            content_type = content_types.get(file_extension, 'application/octet-stream')
            
            # Conditions for the upload
            conditions = [
                ["content-length-range", 1, file_size + 1024*1024],  # Allow 1MB overhead
                {"x-amz-meta-upload-id": upload_id},
                {"x-amz-meta-model-name": model_name},
                {"x-amz-meta-model-version": version},
                {"x-amz-meta-uploaded-by": uploaded_by},
                {"x-amz-server-side-encryption": "AES256"},
                {"x-amz-meta-upload-timestamp": upload_timestamp},
                {"Content-Type": content_type}
            ]
            
            # Fields to include in the upload
            fields = {
                "Content-Type": content_type,
                "x-amz-meta-upload-id": upload_id,
                "x-amz-meta-model-name": model_name,
                "x-amz-meta-model-version": version,
                "x-amz-meta-uploaded-by": uploaded_by,
                "x-amz-meta-upload-timestamp": upload_timestamp,
                "x-amz-server-side-encryption": "AES256"
            }
            
            # Generate presigned POST
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expires_in
            )
            
            # Store upload info
            upload_info = {
                "upload_id": upload_id,
                "s3_key": s3_key,
                "model_name": model_name,
                "version": version,
                "file_size": file_size,
                "uploaded_by": uploaded_by,
                "created_at": datetime.now().isoformat(),
                "expires_at": expiration_time.isoformat(),
                "status": "pending"
            }
            
            self._store_upload_info(upload_id, upload_info, expires_in)
            
            logger.info(f"Generated presigned upload URL for {model_name} v{version}, upload_id: {upload_id}")
            
            return {
                "upload_id": upload_id,
                "upload_url": response["url"],
                "upload_fields": response["fields"],
                "s3_key": s3_key,
                "expires_at": expiration_time
            }
            
        except ClientError as e:
            logger.error(f"Error generating presigned upload URL: {str(e)}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")

    def verify_upload(self, s3_key: str) -> Dict[str, Any]:
        """
        Verify that a file was successfully uploaded to S3
        
        Args:
            s3_key: The S3 key to check
        
        Returns:
            Dictionary with verification details
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return {
                "exists": True,
                "size": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType"),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
                "server_side_encryption": response.get("ServerSideEncryption")
            }
        except ClientError as e:
            print(e)
            if e.response['Error']['Code'] == '404':
                return {"exists": False}
            logger.error(f"Error verifying upload: {str(e)}")
            raise

    def generate_download_url(
        self,
        s3_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a presigned URL for downloading the model
        
        Args:
            s3_key: The S3 key of the model file
            expires_in: URL expiration time in seconds
            filename: Optional filename for Content-Disposition header
        
        Returns:
            Presigned URL for downloading
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key
            }
            
            # Add Content-Disposition header if filename provided
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            logger.info(f"Generated presigned download URL for: {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned download URL: {str(e)}")
            raise

    def delete_model_file(self, s3_key: str) -> bool:
        """
        Delete a model file from S3
        
        Args:
            s3_key: The S3 key of the model file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted AI model from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting AI model from S3: {str(e)}")
            return False

    def list_model_files(
        self,
        model_name: Optional[str] = None,
        version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List model files in S3
        
        Args:
            model_name: Optional filter by model name
            version: Optional filter by version
        
        Returns:
            List of model files with metadata
        """
        try:
            prefix = self.models_prefix
            if model_name:
                clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_name)
                prefix = f"{self.models_prefix}/{clean_name}"
                if version:
                    clean_version = "".join(c if c.isalnum() or c in "-_." else "_" for c in version)
                    prefix = f"{prefix}/{clean_version}"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag']
                    })
            
            return files
        except ClientError as e:
            logger.error(f"Error listing model files: {str(e)}")
            return []

    def get_object_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata for an S3 object
        
        Args:
            s3_key: The S3 key
        
        Returns:
            Object metadata
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {}),
                'server_side_encryption': response.get('ServerSideEncryption')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            logger.error(f"Error getting object metadata: {str(e)}")
            raise

    def copy_model_file(
        self,
        source_key: str,
        dest_key: str
    ) -> bool:
        """
        Copy a model file within S3 (useful for versioning)
        
        Args:
            source_key: Source S3 key
            dest_key: Destination S3 key
        
        Returns:
            True if successful
        """
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
                ServerSideEncryption='AES256'
            )
            logger.info(f"Copied model from {source_key} to {dest_key}")
            return True
        except ClientError as e:
            logger.error(f"Error copying model file: {str(e)}")
            return False

    # ============================================================================
    # UPLOAD TRACKING METHODS
    # ============================================================================

    def _store_upload_info(
        self,
        upload_id: str,
        upload_info: Dict[str, Any],
        ttl: int
    ):
        """Store upload info in Redis or memory"""
        if self.redis_available:
            self.redis_client.setex(
                f"upload:{upload_id}",
                ttl,
                json.dumps(upload_info)
            )
        else:
            self.pending_uploads[upload_id] = upload_info

    def get_upload_info(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get upload info from Redis or memory"""
        if self.redis_available:
            data = self.redis_client.get(f"upload:{upload_id}")
            return json.loads(data) if data else None
        else:
            return self.pending_uploads.get(upload_id)

    def mark_upload_complete(self, upload_id: str) -> bool:
        """Mark an upload as complete"""
        upload_info = self.get_upload_info(upload_id)
        if upload_info:
            upload_info["status"] = "completed"
            upload_info["completed_at"] = datetime.now().isoformat()
            self._store_upload_info(upload_id, upload_info, 3600)  # Keep for 1 hour
            return True
        return False

    def cleanup_upload(self, upload_id: str) -> bool:
        """Clean up upload tracking data"""
        if self.redis_available:
            return bool(self.redis_client.delete(f"upload:{upload_id}"))
        else:
            if upload_id in self.pending_uploads:
                del self.pending_uploads[upload_id]
                return True
            return False

    def cleanup_expired_uploads(self):
        """Clean up expired uploads (for in-memory storage)"""
        if not self.redis_available:
            now = datetime.now()
            expired = []
            for upload_id, info in self.pending_uploads.items():
                expires_at = datetime.fromisoformat(info["expires_at"])
                if now > expires_at:
                    expired.append(upload_id)
            
            for upload_id in expired:
                del self.pending_uploads[upload_id]
                logger.info(f"Cleaned up expired upload: {upload_id}")


# Initialize singleton instance
ai_model_s3_manager = AIModelS3Manager()