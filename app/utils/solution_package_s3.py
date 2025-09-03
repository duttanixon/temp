# app/utils/solution_package_s3.py
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from app.core.config import settings
from app.utils.logger import get_logger
import json

logger = get_logger("utils.solution_package_s3")


class SolutionPackageS3Manager:
    """Manager for solution package S3 operations with direct upload support"""
    
    def __init__(self):
        """Initialize S3 client for package uploads"""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = settings.S3_SOLUTION_PACKAGE_BUCKET
        
        # In-memory storage for tracking uploads (can be replaced with Redis)
        self.pending_uploads = {}
        
        logger.info(f"SolutionPackageS3Manager initialized with bucket: {self.bucket_name}")

    def generate_s3_key(
        self,
        solution_name: str,
        package_name: str,
        version: str,
        device_type: str,
        accelarator_type: Optional[str],
        file_extension: str
    ) -> str:
        """
        Generate S3 key for solution package
        """
        # Clean name and version for S3 key
        solution_name = solution_name.replace(" ", "_").lower()
        clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in package_name)
        clean_version = "".join(c if c.isalnum() or c in "-_." else "_" for c in version)
        
        s3_key = f"{solution_name}/{device_type}/{accelarator_type}/{clean_name}_{clean_version}{file_extension}"
        return s3_key

    def generate_presigned_upload(
        self,
        solution_id: str,
        solution_name: str,
        package_name: str,
        version: str,
        device_type: str,
        accelarator_type: str,
        file_extension: str,
        file_size: int,
        uploaded_by: str,
        expires_in: int = 1800  # 30 minutes default
    ) -> Dict[str, Any]:
        """
        Generate a presigned POST URL for direct S3 upload
        
        Args:
            solution_id: Solution ID this package belongs to
            package_name: Name of the package
            version: Version of the package
            device_type: Target platform
            accelarator_type:  accelerator type
            file_extension: File extension
            file_size: Expected file size in bytes
            uploaded_by: Email of the uploader
            expires_in: URL expiration time in seconds
        
        Returns:
            Dictionary with upload URL, fields, and metadata
        """
        upload_id = str(uuid.uuid4())
        s3_key = self.generate_s3_key(
            solution_name=solution_name,
            package_name=package_name,
            version=version,
            device_type=device_type,
            accelarator_type=accelarator_type,
            file_extension=file_extension
        )
        expiration_time = datetime.now() + timedelta(seconds=expires_in)
        
        try:
            # Content type mapping for common package formats
            content_types = {
                '.tar.gz': 'application/gzip',
                '.tar': 'application/x-tar',
                '.zip': 'application/zip',
                '.deb': 'application/x-debian-package',
                '.rpm': 'application/x-rpm',
                '.AppImage': 'application/x-executable',
                '.exe': 'application/x-msdownload',
                '.msi': 'application/x-msi',
                '.pkg': 'application/x-newton-compatible-pkg',
                '.dmg': 'application/x-apple-diskimage',
                '.jar': 'application/java-archive',
                '.war': 'application/java-archive',
                '.ear': 'application/java-archive',
                '.whl': 'application/zip',
                '.egg': 'application/zip'
            }
            content_type = content_types.get(file_extension, 'application/octet-stream')
            
            # Generate presigned POST
            conditions = [
                {"content-type": content_type},
                ["content-length-range", 1, file_size + 1024*1024],  # Allow 1MB overhead
                {"x-amz-meta-uploaded-by": uploaded_by},
                {"x-amz-meta-package-name": package_name},
                {"x-amz-meta-package-version": version},
                {"x-amz-meta-solution-id": str(solution_id)}
            ]
            
            fields = {
                "Content-Type": content_type,
                "x-amz-meta-uploaded-by": uploaded_by,
                "x-amz-meta-package-name": package_name,
                "x-amz-meta-package-version": version,
                "x-amz-meta-solution-id": str(solution_id)
            }
            
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expires_in
            )
            
            # Store upload info for tracking
            upload_info = {
                "upload_id": upload_id,
                "s3_key": s3_key,
                "solution_id": str(solution_id),
                "package_name": package_name,
                "version": version,
                "uploaded_by": uploaded_by,
                "expires_at": expiration_time.isoformat(),
                "status": "pending"
            }
            self.pending_uploads[upload_id] = upload_info
            
            return {
                "upload_id": upload_id,
                "upload_url": response["url"],
                "upload_fields": response["fields"],
                "s3_key": s3_key,
                "expires_at": expiration_time
            }
            
        except ClientError as e:
            logger.error(f"Error generating presigned upload URL: {str(e)}")
            raise

    def verify_upload(self, s3_key: str) -> Dict[str, Any]:
        """
        Verify that a file was uploaded to S3
        
        Args:
            s3_key: S3 key to check
        
        Returns:
            Dictionary with verification results
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "exists": True,
                "size": response["ContentLength"],
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType"),
                "metadata": response.get("Metadata", {})
            }
            
        except ClientError as e:
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
        Generate a presigned URL for downloading a package
        
        Args:
            s3_key: S3 key of the package
            expires_in: URL expiration time in seconds
            filename: Optional filename for download
        
        Returns:
            Presigned download URL
        """
        try:
            params = {
                "Bucket": self.bucket_name,
                "Key": s3_key
            }
            
            if filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
            
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Error generating download URL: {str(e)}")
            raise

    def delete_package_file(self, s3_key: str) -> bool:
        """
        Delete a package file from S3
        
        Args:
            s3_key: S3 key of the file to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted package file: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting package file: {str(e)}")
            return False

    def copy_package(
        self,
        source_key: str,
        destination_key: str
    ) -> bool:
        """
        Copy a package file within S3 (useful for versioning)
        
        Args:
            source_key: Source S3 key
            destination_key: Destination S3 key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )
            
            logger.info(f"Copied package from {source_key} to {destination_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error copying package: {str(e)}")
            return False

    def list_package_versions(
        self,
        solution_id: str,
        package_name: str,
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a package for a solution
        
        Args:
            solution_id: Solution ID
            package_name: Package name
        
        Returns:
            List of package versions with metadata
        """
        prefix = f"solutions/{solution_id}/packages/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            packages = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Parse package info from key
                    if package_name in key:
                        packages.append({
                            's3_key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                        })
            
            return packages
            
        except ClientError as e:
            logger.error(f"Error listing package versions: {str(e)}")
            return []

    def mark_upload_complete(self, upload_id: str) -> bool:
        """Mark an upload as complete"""
        if upload_id in self.pending_uploads:
            self.pending_uploads[upload_id]["status"] = "complete"
            return True
        return False

    def cancel_upload(self, upload_id: str) -> bool:
        """Cancel a pending upload"""
        if upload_id in self.pending_uploads:
            del self.pending_uploads[upload_id]
            return True
        return False

    def cleanup_expired_uploads(self):
        """Clean up expired uploads"""
        now = datetime.now()
        expired = []
        for upload_id, info in self.pending_uploads.items():
            expires_at = datetime.fromisoformat(info["expires_at"])
            if now > expires_at and info["status"] == "pending":
                expired.append(upload_id)
        
        for upload_id in expired:
            del self.pending_uploads[upload_id]
            logger.info(f"Cleaned up expired package upload: {upload_id}")


# Initialize singleton instance
solution_package_s3_manager = SolutionPackageS3Manager()