import boto3
from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.logger import get_logger
import uuid
import time

logger = get_logger(__name__)


class KVSManager:
    """Manager for AWS Kinesis Video Streams operations"""
    
    def __init__(self):
        self.kvs_client = boto3.client(
            "kinesisvideo",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.kvs_media_client = None
        logger.info("KVS Manager initialized")

    def generate_stream_name(self, device_name: str) -> str:
        """Generate a unique stream name for the device"""
        # Format: device-{device_name}-{timestamp}
        # This ensures uniqueness and makes streams identifiable
        timestamp = int(time.time())
        return f"device-{device_name}-{timestamp}"
    

    def check_stream_exists(self, stream_name: str) -> bool:
        """Check if a KVS stream exists"""
        try:
            self.kvs_client.describe_stream(StreamName=stream_name)
            return True
        except self.kvs_client.exceptions.ResourceNotFoundException:
            return False
        except Exception as e:
            logger.error(f"Error checking stream existence: {str(e)}")
            return False


    def create_stream_if_not_exists(self, stream_name: str) -> bool:
        """Create a KVS stream if it doesn't exist"""
        try:
            if not self.check_stream_exists(stream_name):
                self.kvs_client.create_stream(
                    StreamName=stream_name,
                    DataRetentionInHours=24,  # Keep recordings for 24 hours
                    MediaType="video/h264"
                )
                logger.info(f"Created KVS stream: {stream_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating stream: {str(e)}")
            return False
        

    def get_stream_endpoint(self, stream_name: str, api_name: str = "GET_HLS_STREAMING_SESSION_URL") -> Optional[str]:
        """Get the endpoint URL for accessing the stream"""
        try:
            response = self.kvs_client.get_data_endpoint(
                StreamName=stream_name,
                APIName=api_name
            )
            return response.get("DataEndpoint")
        except Exception as e:
            logger.error(f"Error getting stream endpoint: {str(e)}")
            return None
        
    def get_hls_streaming_url(self, stream_name: str) -> Optional[Dict[str, str]]:
        """Get HLS streaming URL for the stream"""
        try:
            # First get the endpoint
            endpoint = self.get_stream_endpoint(stream_name, "GET_HLS_STREAMING_SESSION_URL")
            if not endpoint:
                return None

            # Create a client for the specific endpoint
            kvs_archived_media_client = boto3.client(
                "kinesis-video-archived-media",
                endpoint_url=endpoint,
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            # Get HLS streaming session URL
            response = kvs_archived_media_client.get_hls_streaming_session_url(
                StreamName=stream_name,
                PlaybackMode="LIVE",
                HLSFragmentSelector={
                    "FragmentSelectorType": "SERVER_TIMESTAMP"
                },
                ContainerFormat="FRAGMENTED_MP4",
                DiscontinuityMode="ALWAYS",
                DisplayFragmentTimestamp="NEVER",
                Expires=3600  # URL expires in 1 hour
            )

            return {
                "hls_url": response.get("HLSStreamingSessionURL"),
                "expires_in": 3600
            }
        except Exception as e:
            logger.error(f"Error getting HLS URL: {str(e)}")
            return None
        

    def delete_stream(self, stream_name: str) -> bool:
        """Delete a KVS stream"""
        try:
            self.kvs_client.delete_stream(StreamName=stream_name)
            logger.info(f"Deleted KVS stream: {stream_name}")
            return True
        except self.kvs_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Stream {stream_name} not found for deletion")
            return True
        except Exception as e:
            logger.error(f"Error deleting stream: {str(e)}")
            return False
        

    def list_active_streams(self) -> list:
        """List all active KVS streams"""
        try:
            streams = []
            next_token = None
            
            while True:
                if next_token:
                    response = self.kvs_client.list_streams(NextToken=next_token)
                else:
                    response = self.kvs_client.list_streams()
                
                streams.extend(response.get("StreamInfoList", []))
                
                next_token = response.get("NextToken")
                if not next_token:
                    break
                    
            return streams
        except Exception as e:
            logger.error(f"Error listing streams: {str(e)}")
            return []


# Initialize the KVS manager
kvs_manager = KVSManager()