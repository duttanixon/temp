
"""
Stream manager module for CityEye solution.
Handles KVS streaming operations functionality.
"""
from typing import Any, Dict, Optional, Tuple
import os
import cv2
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from core.implementation.solutions.city_eye.kvs_stream_handler import KVSStreamHandler
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ProcessingError

logger = get_logger()

class StreamManager:
    """Manages streaming operations for CityEye solution."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize stream manager.
        
        Args:
            config: Configuration for streaming
        """
        self.component_name = self.__class__.__name__
        self.config = config
        # KVS handler
        self.kvs_handler: Optional[KVSStreamHandler] = None
        self.kvs_lock = threading.Lock()

        self._initialize_kvs_handler()

        logger.info("StreamManager initialized", component=self.component_name)


    def _initialize_kvs_handler(self) -> bool:
        """
        Initialize KVS output handler if not already initialized.
        
        Returns:
            True if successful, False otherwise
        """
        if self.kvs_handler is not None:
            return True
        
        try:
            self.kvs_handler = KVSStreamHandler(self.config)
            logger.info("KVS output handler initialized", component=self.component_name)
            return True
        except Exception as e:
            logger.error(
                "Failed to initialize KVS handler",
                exception=e,
                component=self.component_name
            )
            self.kvs_handler = None
            return False


    def start_stream(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Start KVS streaming.
        
        Args:
            stream_name: Name of the stream to start
            
        Returns:
            Tuple of (success, error_message)
        """
        
        with self.kvs_lock:
            
            if self.kvs_handler and self.kvs_handler.is_streaming:
                return False, "already_streaming"
            
            if not self._initialize_kvs_handler():
                return False, "failed_to_initialize"
            
            try:
                stream_name = payload.get("stream_name")
                duration_seconds = payload.get("duration_seconds", 240)
                stream_quality = payload.get("stream_quality", "medium")
                
                # Clear any existing frames in KVS handler queue before starting
                if hasattr(self.kvs_handler, 'clear_frame_queue'):
                    self.kvs_handler.clear_frame_queue()

                # Start KVS streaming
                success = self.kvs_handler.start_streaming(
                    stream_name=stream_name,
                    duration_seconds=duration_seconds,
                    stream_quality=stream_quality                    
                )# this block the frame processing thread until the stream is started or failed
                
                if success:
                    logger.info(
                        f"KVS streaming started successfully",
                        context={
                            "stream_name": stream_name,
                            "duration": duration_seconds,
                            "quality": stream_quality
                        },
                        component=self.component_name
                    )
                    return True, None
                else:
                    return False, None
                
            except Exception as e:
                logger.error(
                    "Failed to start KVS streaming",
                    exception=e,
                    context={"stream_name": stream_name},
                    component=self.component_name
                )
                return False, str(e)
    
    def stop_stream(self) -> Tuple[bool, Optional[str]]:
        """
        Stop KVS streaming.
        
        Returns:
            Tuple of (success, error_message)
        """
        with self.kvs_lock:
            if not self.kvs_handler:
                return False, "KVS handler not initialized"

            if not self.kvs_handler.is_streaming:
                return False, "No active stream to stop"
            
            try:
                success = self.kvs_handler.stop_streaming()
                if success:
                    logger.info(
                        "KVS streaming stopped successfully",
                        component=self.component_name
                    )
                    return True, None
                else:
                    return False, None
                
            except Exception as e:
                logger.error(
                    "Failed to stop KVS streaming",
                    exception=e,
                    component=self.component_name
                )
                return False, str(e)


    def get_kvs_handler(self) -> Optional[KVSStreamHandler]:
        """
        Get the KVS handler instance.
        
        Returns:
            KVSStreamHandler instance if initialized, None otherwise
        """
        with self.kvs_lock:
            return self.kvs_handler if self.kvs_handler else None

    def cleanup(self):
        """Cleanup streaming resources."""
        if self.kvs_handler:
            try:
                self.kvs_handler.cleanup()
            except Exception as e:
                logger.error(
                    "Error cleaning up KVS handler",
                    exception=e,
                    component=self.component_name
                )